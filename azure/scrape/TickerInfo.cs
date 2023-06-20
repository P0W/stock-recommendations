public class TickerInfo
{
    public bool NegativeComment { get; set; }
    public int BuyRecommendationPercentage { get; set; }
    public string? StockInfo { get; set; }
    public string? Ticker { get; set; }
    public string? StockName { get; set; }
    public List<string> Tags { get; set; } = new List<string>();
    public Dictionary<string, dynamic> screenerRatio = new();
}

