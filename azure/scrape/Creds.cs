using Newtonsoft.Json;

public class Creds
{
    public string? ENDPOINT { get; set; }
    public string? PRIMARYKEY { get; set; }
    public string? DATABASE { get; set; }
    public string? CONTAINER { get; set; }

    [JsonConstructor]
    public Creds(string endpoint, string primaryKey, string database, string container)
    {
        ENDPOINT = endpoint;
        PRIMARYKEY = primaryKey;
        DATABASE = database;
        CONTAINER = container;
    }
}
