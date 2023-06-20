using HtmlAgilityPack;
using Microsoft.Azure.Cosmos;
using Newtonsoft.Json;


class Program
{
    private static string? ENDPOINT; // = "https://screener-tickertape.documents.azure.com:443/";
    private static string? PRIMARYKEY;
    private static string? DATABASE; // = "scrapedDb";
    private static string? CONTAINER; // = "results";

    private static readonly HttpClient client = new();

    public static void Setup()
    {
        // Read json file creds.json  to  get primary key and endpoint
        // creds location is in the same folder as the program, take form enviroment variable of csproj file
        Creds? creds = JsonConvert.DeserializeObject<Creds>(File.ReadAllText("creds.json"));
        if (creds != null)
        {
            ENDPOINT = creds.ENDPOINT;
            PRIMARYKEY = creds.PRIMARYKEY;
            DATABASE = creds.DATABASE;
            CONTAINER = creds.CONTAINER;
        }

        client.DefaultRequestHeaders.UserAgent.ParseAdd("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3");
        client.DefaultRequestHeaders.Referrer = new Uri("https://www.google.com/");
    }

    static async Task<List<(string, string)>> GetIndexStocksAsync(string indexUrl)
    {
        // Create an HttpClient object and set the user agent and referer headers to mimic a web browser
        //HttpClient client = new HttpClient();
        // Send a GET request to the index page
        HttpResponseMessage response = await client.GetAsync(indexUrl);
        string responseContent = await response.Content.ReadAsStringAsync();

        // Parse the HTML content using HtmlAgilityPack
        HtmlDocument doc = new HtmlDocument();
        doc.LoadHtml(responseContent);

        // Select the list of stocks and extract their names and URLs
        List<(string, string)> stocksList = new List<(string, string)>();
        var stockLinks = doc.DocumentNode.SelectNodes("//a[contains(@class, 'constituent-name')]");
        if (stockLinks != null)
        {
            foreach (var link in stockLinks)
            {
                string stockName = link.InnerText;
                string stockUrl = link.GetAttributeValue("href", "");
                stocksList.Add((stockName, "https://www.tickertape.in" + stockUrl));
            }
        }

        return stocksList;
    }

    public static async Task<TickerInfo> GetContents(string page)
    {
        var tickerInfo = new TickerInfo
        {
            Ticker = "NOSYMBOL",
        };

        try
        {
            var response = await client.GetAsync(page);
            if (response.IsSuccessStatusCode)
            {
                var content = await response.Content.ReadAsStringAsync();
                var document = new HtmlDocument();
                //document.LoadHtml(content);
                var loadTask = Task.Run(() => document.LoadHtml(content));
                if (await Task.WhenAny(loadTask, Task.Delay(2000)) == loadTask)
                {
                    // The LoadHtml method completed before the timeout
                }
                else
                {
                    // Log an error message
                    Console.WriteLine($"Failed loading {page}");
                    return tickerInfo;
                }

                tickerInfo.Ticker = document.DocumentNode
                    .SelectSingleNode("//span[contains(@class, 'ticker')]")?.InnerText;

                tickerInfo.Ticker = HtmlEntity.DeEntitize(tickerInfo.Ticker);

                var negativeCommentNode = document.DocumentNode
                    .SelectSingleNode("//span[contains(@class, 'icon-negative-comment')]");
                tickerInfo.NegativeComment = negativeCommentNode != null;

                var recommendationNode = document.DocumentNode
                    .SelectSingleNode("//span[contains(@class, 'percBuyReco-value')]");

                // Set BuyRecommendationPercentage to 0 if the node is null
                tickerInfo.BuyRecommendationPercentage = recommendationNode != null
                    ? int.Parse(recommendationNode.InnerText.Replace("%", ""))
                    : 0;

                var staockLabelTitles = document.DocumentNode
                    .SelectNodes("//span[contains(@class, 'stock-label-title')]");

                if (staockLabelTitles != null)
                {
                    foreach (var node in staockLabelTitles)
                    {
                        if (node.InnerText.Contains("cap"))
                        {
                            tickerInfo.StockInfo = node.InnerText;
                            break;
                        }
                    }
                }
                var badgeList = document.DocumentNode.SelectNodes("//span[contains(@class, 'badge')]");
                int goodCount = 0;
                if (badgeList != null)
                {
                    for (int i = 0; i < Math.Min(6, badgeList.Count); i++)
                    {
                        string badgeValue = badgeList[i].InnerHtml;
                        if (badgeValue.Contains("Good") || badgeValue.Contains("High"))
                        {
                            goodCount += 1;
                        }
                        tickerInfo.Tags.Add(badgeValue);
                    }
                    tickerInfo.Tags.Add("Good Count = " + goodCount.ToString());
                }

            }
            else
            {
                Console.WriteLine($"Failed parsing {page}");
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error {ex.Message}");
        }

        return tickerInfo;
    }

    public static async Task<bool> HasNegativeCommentAsync(string page)
    {
        List<string> financialsList = new List<string> {
            "holdings",
            "financialschecklist=basic&period=annual&statement=balancesheet&view=normal",
            "financials?checklist=basic&period=annual&statement=cashflow",
            "financials?checklist=basic&period=annual&statement=income&view=normal"
        };
        // loop over the financials list and check if there is a negative comment
        foreach (var financials in financialsList)
        {
            var url = $"{page}/{financials}";
            var response = await client.GetAsync(url);
            if (response.IsSuccessStatusCode)
            {
                var doc = new HtmlDocument();
                var content = await response.Content.ReadAsStringAsync();
                doc.LoadHtml(content);
                // Find any tags with class "icon-negative-comment"
                var hasNegComment = doc.DocumentNode.SelectNodes("//i[contains(@class, 'icon-negative-comment')]")?.Count > 0;
                if (hasNegComment)
                {
                    return true;
                }
            }
            else
            {
                Console.WriteLine($"Failed parsing {page}");
            }
        }
        return false;
    }

    // Method to stripoff %, "," and "Rs." from the string
    private static string StripOff(string str)
    {
        return HtmlEntity.DeEntitize(str).Replace("%", "").Replace(",", "").Replace("Rs.", "").Trim();
    }

    // Method ot parse either float or int from the string based on template arg
    private static T? Parse<T>(string str)
    {
        try
        {
            if (typeof(T) == typeof(float))
            {
                return (T)(object)float.Parse(str);
            }
            else if (typeof(T) == typeof(int))
            {
                return (T)(object)int.Parse(str);
            }
            else
            {
                throw new Exception("Invalid type");
            }
        }
        catch
        {
            return default;
        }
    }

    public static async Task<Dictionary<string, dynamic>> GetRatioFromScreener(string? ticker)
    {
        var page = $"https://www.screener.in/company/{ticker}/consolidated/";
        var result = new Dictionary<string, dynamic>()
        {
            ["roce"] = "N/A",
            ["roe"] = "N/A",
            ["market_cap"] = "N/A",
            ["cons"] = 0,
            ["price_to_book"] = 0
        };
        if (string.IsNullOrEmpty(ticker))
        {
            return result;
        }
        var tries = 0;
        //var httpClient = new HttpClient();
        while (tries < 15)
        {
            var res = await client.GetAsync(page);
            if (res.IsSuccessStatusCode)
            {
                var html = await res.Content.ReadAsStringAsync();
                var doc = new HtmlDocument();
                doc.LoadHtml(html);
                float cmp = 0.0f;
                var ratios = doc.DocumentNode.SelectNodes("//*[@id='top-ratios']/li/span/span");
                foreach (var (ratio, idx) in ratios.Select((r, i) => (r, i)))
                {
                    try // 2 and 3 are high and low value
                    {
                        if (idx == 7) // Hard coded rows from Screener.in
                        {
                            result["roce"] = Parse<float>(StripOff(ratio.InnerHtml));
                        }
                        if (idx == 8)
                        {
                            result["roe"] = Parse<float>(StripOff(ratio.InnerHtml));
                        }
                        if (idx == 0)
                        {
                            result["market_cap"] = Parse<int>(StripOff(ratio.InnerHtml));
                        }
                        if (idx == 1)
                        {
                            // Stripoff the comma and convert to float
                            cmp = Parse<float>(StripOff(ratio.InnerHtml));
                        }
                        if (idx == 5)
                        {
                            var bookValue = Parse<float>(StripOff(ratio.InnerHtml));
                            result["price_to_book"] = (float)Math.Ceiling(cmp / bookValue);
                        }
                    }
                    catch (Exception e)
                    {
                        Console.WriteLine($"Error {e}, {ticker}, {ratio.InnerHtml}");
                    }
                }
                var consDiv = doc.DocumentNode.SelectSingleNode("//div[@class='cons']");

                // Count the number of <li> tags within the div
                if (consDiv != null)
                {
                    var liTags = consDiv.SelectNodes(".//li");
                    if (liTags != null)
                    {
                        result["cons"] = liTags.Count;
                    }
                }
                break;
            }
            else
            {
                tries += 1;
                await Task.Delay(TimeSpan.FromSeconds(tries));
            }
        }
        return result;
    }

    // Facade to call GetContents, GetRatioFromScreener and HasNegativeCommentAsync
    public static async Task<TickerInfo> GetTickerInfo(string stockUrl, string stockName)
    {
        // Display on console the ticker
        Console.WriteLine($"Processing {stockName}");
        var tickerInfo = await GetContents(stockUrl);
        if (tickerInfo.Ticker != "NOSYMBOL")
        {
            tickerInfo.StockName = stockName;
            tickerInfo.NegativeComment = await HasNegativeCommentAsync(stockUrl);
            tickerInfo.screenerRatio = await GetRatioFromScreener(tickerInfo.Ticker);
        }
        else
        {
            Console.WriteLine($"Ticker not found for {stockUrl}");
        }
        return tickerInfo;
    }

    static async void Test()
    {
        var testUrl = "https://www.tickertape.in/stocks/fortis-healthcare-FOHE";
        var resuls = await GetContents(testUrl);
        // Display resuls
        Console.WriteLine($"Ticker: {resuls.Ticker}");
        Console.WriteLine($"NegativeComment: {resuls.NegativeComment}");
        Console.WriteLine($"StockInfo: {resuls.StockInfo}");
        Console.WriteLine($"BuyRecommendationPercentage : {resuls.BuyRecommendationPercentage}");
        Console.WriteLine($"Tags: {string.Join(",", resuls.Tags)}");

        var screenerResults = GetRatioFromScreener(resuls.Ticker);
        // Display screenerResults
        Console.WriteLine($"roce: {screenerResults.Result["roce"]}");
        Console.WriteLine($"roe: {screenerResults.Result["roe"]}");
        Console.WriteLine($"market_cap: {screenerResults.Result["market_cap"]}");
        Console.WriteLine($"cons: {screenerResults.Result["cons"]}");
        Console.WriteLine($"price_to_book: {screenerResults.Result["price_to_book"]}");


        var fins = await HasNegativeCommentAsync(testUrl);
        // Display fins
        Console.WriteLine($"NegativeComment: {fins}");


        // Exit
        Environment.Exit(0);
    }

    static async Task Main(string[] args)
    {

        Setup();

        // parse argument --stockUrl=50 or --stockUrl=500. Match the argument name
        if (args.Length == 0)
        {
            Console.WriteLine("Usage: --stockUrl=50 or --stockUrl=500");
            Test();
            Console.ReadLine();
            Environment.Exit(1);
        }

        var stockList = args[0].Split("=")[1];

        var nifty50Url = "https://www.tickertape.in/indices/nifty-50-index-.NSEI/constituents?type=marketcap";
        var nifty500Url = "https://www.tickertape.in/indices/nifty-500-index-.NIFTY500/constituents?type=marketcap";

        string stockUrl = "";

        if (stockList == "50")
        {
            stockUrl = nifty50Url;
        }
        else if (stockList == "500")
        {
            stockUrl = nifty500Url;
        }
        else
        {
            Console.WriteLine("Invalid stock list. Exiting");
            Environment.Exit(1);
        }

        List<(string, string)> stocks = await GetIndexStocksAsync(stockUrl);
        // Set the maximum number of concurrent tasks
        int maxConcurrency = 25;

        // Create a SemaphoreSlim object to control the maximum number of concurrent tasks
        SemaphoreSlim semaphore = new SemaphoreSlim(maxConcurrency);

        // Process the URLs using a thread pool
        List<Task<TickerInfo>> tasks = new();
        foreach ((string, string) stock in stocks)
        {
            await semaphore.WaitAsync();

            Task<TickerInfo> task = Task.Run(async () =>
            {
                try
                {
                    return await GetTickerInfo(stock.Item2, stock.Item1);
                }
                finally
                {
                    semaphore.Release();
                }
            });

            tasks.Add(task);
        }

        // Wait for all the tasks to complete
        TickerInfo[] results = await Task.WhenAll(tasks);

        // Filter NOSYMBOL and null
        results = results.Where(x => x.Ticker != "NOSYMBOL" && x.Ticker != null).ToArray();

        // Display count 
        Console.WriteLine($"Total parsed paged: {results.Length}");

        var client = new CosmosClient(ENDPOINT, PRIMARYKEY);
        var database = client.GetDatabase(DATABASE);
        var container = database.GetContainer(CONTAINER);

        // Remove all items from the container
        await container.DeleteContainerAsync();

        // Create a new container
        await database.CreateContainerIfNotExistsAsync(CONTAINER, partitionKeyPath: "/ticker");

        // loop over the results array
        foreach (TickerInfo result in results)
        {
            try
            {
                // Create a ResultsModel object
                ResultsModel resultsModel = new ResultsModel
                {
                    Ticker = result.Ticker,
                    HasNegativeComments = result.NegativeComment,
                    RecommCount = result.BuyRecommendationPercentage,
                    Info = result.StockInfo,
                    Stock = result.StockName,
                    AvgScore = result.Tags.Count(tag => tag == "Avg" || tag == "Good"),

                    ConsCount = result.screenerRatio["cons"],
                    MarketCap = result.screenerRatio["market_cap"],
                    Price_To_book = result.screenerRatio["price_to_book"],
                    ROCE = result.screenerRatio["roce"],
                    ROE = result.screenerRatio["roe"],

                    Date = DateTime.Now.ToString(),
                    Id = Guid.NewGuid().ToString()
                };
                await container.CreateItemAsync(resultsModel, partitionKey: new PartitionKey(resultsModel.Ticker));
                Console.WriteLine($"Added record: {resultsModel?.Ticker}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error adding record: {result?.Ticker} to cosmosdb");
                Console.WriteLine($"Error: {ex.Message}");
            }
        }
    }
}
