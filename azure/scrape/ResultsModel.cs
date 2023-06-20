using Newtonsoft.Json;

public class ResultsModel
{
    [JsonProperty(PropertyName = "id")]
    public string? Id { get; set; }

    // Add datetime field
    [JsonProperty(PropertyName = "date")]
    public string? Date { get; set; }

    [JsonProperty(PropertyName = "stock")]
    public string? Stock { get; set; }

    [JsonProperty(PropertyName = "ticker")]
    public string? Ticker { get; set; }

    [JsonProperty(PropertyName = "info")]
    public string? Info { get; set; }

    [JsonProperty(PropertyName = "avgScore")]
    public int AvgScore { get; set; }

    [JsonProperty(PropertyName = "hasNegativeComment")]
    public bool HasNegativeComments { get; set; }

    [JsonProperty(PropertyName = "market_cap")]
    public int MarketCap { get; set; }

    [JsonProperty(PropertyName = "roce")]
    public float ROCE { get; set; }

    [JsonProperty(PropertyName = "roe")]
    public float ROE { get; set; }

    [JsonProperty(PropertyName = "price_to_book")]
    public float Price_To_book { get; set; }

    [JsonProperty(PropertyName = "cons")]
    public int ConsCount { get; set; }

    [JsonProperty(PropertyName = "recom")]
    public int RecommCount { get; set; }
}

