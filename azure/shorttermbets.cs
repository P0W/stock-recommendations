using System;
using System.IO;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Azure.WebJobs;
using Microsoft.Azure.WebJobs.Extensions.Http;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json;
using ScarppedData;
using Microsoft.Azure.Cosmos;

namespace P0W.TickerScreener
{
    public static class shorttermbets
    {
        [FunctionName("shorttermbets")]
        public static async Task<IActionResult> Run(
            [HttpTrigger(AuthorizationLevel.Function, "get", "post", Route = null)] HttpRequest req,
            ILogger log)
        {


            string cons = req.Query["cons"];
            string price_to_book = req.Query["price_to_book"];
            string recom = req.Query["recom"];

            string requestBody = await new StreamReader(req.Body).ReadToEndAsync();
            dynamic data = JsonConvert.DeserializeObject(requestBody);
            cons = cons ?? data?.cons;
            price_to_book ??= data?.price_to_book;
            recom ??= data?.recom;

            // if cons is null or empty, set it to 0
            if (string.IsNullOrEmpty(cons))
            {
                cons = "0";
            }
            // if price_to_book is null or empty, set it to 7
            if (string.IsNullOrEmpty(price_to_book))
            {
                price_to_book = "7";
            }
            // if recom is null or empty, set it to 90
            if (string.IsNullOrEmpty(recom))
            {
                recom = "90";
            }

            log.LogInformation("C# HTTP trigger function processed a request.");
            // Log the query parameters
            log.LogInformation($"cons: {cons} price_to_book: {price_to_book} recom: {recom}");

            string responseMessage = "<table><tr>" +
                    "<th>Stock</th>" +
                    "<th>Ticker</th>" +
                    "<th>Cap Segment</th>" +
                    "<th>Market Cap</th>" +
                    "<th>ROCE</th>" +
                    "<th>ROE</th>" +
                    "<th>P/B</th>" +
                    "<th>Cons Count</th>" +
                    "<th>Recommendation %</th>" +
                    "</tr>";

            // Create a html table with header stock and ticker
            // Read josn file creds.json  to  get primary key and endpoint
            // creds location is in the same folder as the program, take form enviroment variable of csproj file

            try
            {
                Creds creds = null;
                // checked if DBCREDS Environment variable is set
                if (string.IsNullOrEmpty(System.Environment.GetEnvironmentVariable("DBCREDS", EnvironmentVariableTarget.Process)))
                {
                    log.LogInformation("DBCREDS Environment variable is not set");
                    // Reda form Constnats.credsFile
                    creds =  JsonConvert.DeserializeObject<Creds>(File.ReadAllText(Constants.credsFile));

                }
                else
                {
                    creds = JsonConvert.DeserializeObject<Creds>(System.Environment.GetEnvironmentVariable("DBCREDS", EnvironmentVariableTarget.Process));

                }

                var client = new CosmosClient(creds.ENDPOINT, creds.PRIMARYKEY);
                var database = client.GetDatabase(Constants.databaseName);
                var container = database.GetContainer(Constants.containerName);

                // use cons, price_to_book, recom to query the database
                var sqlQueryText = $"SELECT  * FROM c where c.cons = {cons} " +
                    $"and c.price_to_book < {price_to_book} " +
                    $"and c.price_to_book > 0 and c.recom > {recom}";

                var queryDefinition = new QueryDefinition(sqlQueryText);
                // log the queryDefinition as string
                log.LogInformation($"Sql Query: {sqlQueryText}");
                var queryResultSetIterator = container.GetItemQueryIterator<ResultsModel>(queryDefinition);

                while (queryResultSetIterator.HasMoreResults)
                {
                    var currentResultSet = await queryResultSetIterator.ReadNextAsync();
                    // Add header in table Stock, Ticker, Info,MarketCap, ROCE, ROE , Price_To_book, ConsCount, RecommCount as header fields

                    foreach (var result in currentResultSet)
                    {
                        // Add the values of the fields in the table
                        responseMessage += "<tr>" +
                            "<td>" + result.Stock + "</td>" +
                            "<td>" + result.Ticker + "</td>" +
                            "<td>" + result.Info + "</td>" +
                            "<td>" + result.MarketCap + "</td>" +
                            "<td>" + result.ROCE + "</td>" +
                            "<td>" + result.ROE + "</td>" +
                            "<td>" + result.Price_To_book + "</td>" +
                            "<td>" + result.ConsCount + "</td>" +
                            "<td>" + result.RecommCount + "</td>" +
                            "</tr>";
                    }
                }
                responseMessage += "</table>";
            }
            catch (Exception ex)
            {
                responseMessage = "<h1>" + ex.Message + "</h1>";
            }

            return new ContentResult()
            {
                Content = responseMessage,
                ContentType = "text/html",
                StatusCode = 200
            };
        }
    }
}
