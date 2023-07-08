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

        private static readonly string CSSCONTENT = @"
        body {
            font-family: Arial, sans-serif;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th, td {
            padding: 6px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }

        th {
            background-color: #f2f2f2;
        }

        th.sno-column,
        td.sno-column {
            background-color: #e6f2ff;
        }

        @media only screen and (max-width: 500px) {
            table {
                font-size: 10px;
            }
        }
    ";

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
                    "<th class='sno-column'>S.No.</th>" +
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
                    creds = JsonConvert.DeserializeObject<Creds>(File.ReadAllText(Constants.credsFile));

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

                string currentDate = "";
                int sno = 1;
                while (queryResultSetIterator.HasMoreResults)
                {
                    var currentResultSet = await queryResultSetIterator.ReadNextAsync();
                    // Add header in table Stock, Ticker, Info,MarketCap, ROCE, ROE , Price_To_book, ConsCount, RecommCount as header fields
                    foreach (var result in currentResultSet)
                    {
                        // Add the values of the fields in the table
                        if (string.IsNullOrEmpty(currentDate))
                        {
                            currentDate = result.Date;
                            // COnvert the date to IST
                            DateTime date = DateTime.Parse(currentDate);
                            date = date.AddHours(5);
                            date = date.AddMinutes(30);
                            currentDate = date.ToString("dd-MMM-yyyy");
                        }
                        responseMessage += "<tr>" +
                             "<td class='sno-column'>" + sno + "</td>" +
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
                        sno++;
                    }
                }
                responseMessage += "</table>";
                // Add a footer with date
                responseMessage += "<p> Last Modified: " + currentDate + "</p>";


            }
            catch (Exception ex)
            {
                responseMessage = "<h1>" + ex.Message + "</h1>";
            }
            string htmlContent = $"<html><head><style>{CSSCONTENT}</style></head><body>{responseMessage}</body></html>";

            return new ContentResult()
            {
                Content = htmlContent,
                ContentType = "text/html",
                StatusCode = 200
            };
        }
    }
}
