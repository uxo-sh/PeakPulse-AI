using System;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using System.Collections.Generic;
using ui_dashboard.Models;

namespace ui_dashboard.Services
{
    public class ApiService
    {
        private readonly HttpClient _client;
        private const string BaseUrl = "http://localhost:8000";

        public static readonly ApiService Instance = new();

        private ApiService()
        {
            _client = new HttpClient
            {
                Timeout = TimeSpan.FromSeconds(10)
            };
        }

        //   Vérifie si l'API Python est en ligne
        public async Task<bool> CheckHealthAsync()
        {
            try
            {
                var response = await _client.GetStringAsync(
                    $"{BaseUrl}/api/health");
                return response.Contains("ok");
            }
            catch
            {
                return false;
            }
        }

        //   Récupère les tendances d'un domaine
        public async Task<DomainData?> GetTrendsAsync(string domain)
        {
            try
            {
                var json = await _client.GetStringAsync(
                    $"{BaseUrl}/api/trends/{domain}");

                var options = new JsonSerializerOptions
                {
                    PropertyNameCaseInsensitive = true
                };

                var apiData = JsonSerializer.Deserialize<ApiDomainData>(
                    json, options);

                if (apiData == null) return null;

                return ConvertToDomainData(apiData);
            }
            catch
            {
                // Retourne null si l'API est hors ligne
                return null;
            }
        }

        //   Convertit les données API en DomainData
        private static DomainData ConvertToDomainData(ApiDomainData api)
        {
            var genres = new List<GenreItem>();

            if (api.Genres != null)
            {
                foreach (var g in api.Genres)
                {
                    genres.Add(new GenreItem
                    {
                        Name        = g.Name ?? "",
                        Score       = g.Score ?? "",
                        TrendLabel  = g.TrendLabel ?? "",
                        Badge       = g.Badge ?? "",
                        ColorHex    = g.ColorHex ?? "#4fc3f7",
                        IsAlternate = g.IsAlternate,
                        BarWidth    = g.BarWidth
                    });
                }
            }

            return new DomainData
            {
                Title            = api.Title ?? "",
                Subtitle         = api.Subtitle ?? "",
                KpiGenres        = api.KpiGenres ?? "",
                KpiScore         = api.KpiScore ?? "",
                KpiOpportunities = api.KpiOpportunities ?? "",
                KpiPrecision     = api.KpiPrecision ?? "",
                ChartBadge       = api.ChartBadge ?? "",
                BarColor         = api.BarColor ?? "#4fc3f7",
                Heights          = api.Heights ?? "",
                OpportunityCount = api.OpportunityCount ?? "",
                IaRecommendation = api.IaRecommendation ?? "",
                Genres           = genres.ToArray()
            };
        }
    }

    //   Modèle JSON correspondant à l'API Python
    public class ApiDomainData
    {
        public string? Domain { get; set; }
        public string? Title { get; set; }
        public string? Subtitle { get; set; }
        public string? KpiGenres { get; set; }
        public string? KpiScore { get; set; }
        public string? KpiOpportunities { get; set; }
        public string? KpiPrecision { get; set; }
        public string? ChartBadge { get; set; }
        public string? BarColor { get; set; }
        public string? Heights { get; set; }
        public string? OpportunityCount { get; set; }
        public string? IaRecommendation { get; set; }
        public List<ApiGenreItem>? Genres { get; set; }
        public string? Source { get; set; }
    }

    public class ApiGenreItem
    {
        public string? Name { get; set; }
        public string? Score { get; set; }
        public string? TrendLabel { get; set; }
        public string? Badge { get; set; }
        public string? ColorHex { get; set; }
        public bool IsAlternate { get; set; }
        public double BarWidth { get; set; }
    }
}