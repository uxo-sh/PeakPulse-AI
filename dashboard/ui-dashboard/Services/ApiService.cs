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

        //Vérifie si l'API Python est en ligne
        public async Task<bool> CheckHealthAsync()
        {
            try
            {
                var response = await _client.GetStringAsync($"{BaseUrl}/api/health");
                return response.Contains("ok");
            }
            catch
            {
                return false;
            }
        }

        // Récupère les tendances
        public async Task<DomainData?> GetTrendsAsync(string domain)
        {
            try
            {
                var json = await _client.GetStringAsync($"{BaseUrl}/api/trends/{domain}");

                var options = new JsonSerializerOptions
                {
                    PropertyNameCaseInsensitive = true
                };

                var apiData = JsonSerializer.Deserialize<ApiDomainData>(json, options);

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
        public async Task<DomainData?> AnalyzeAsync(string domain)
        {
            try
            {
                // ML pipeline is heavy — use a dedicated client with 5-min timeout
                using var analyzeClient = new HttpClient
                {
                    Timeout = TimeSpan.FromMinutes(5)
                };
                var json = await analyzeClient.GetStringAsync($"{BaseUrl}/api/analyze/{domain}");

                var options = new JsonSerializerOptions
                {
                    PropertyNameCaseInsensitive = true
                };

                var apiData = JsonSerializer.Deserialize<ApiDomainData>(json, options);

                if (apiData == null) return null;

                return ConvertToDomainData(apiData);
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"AnalyzeAsync error: {ex.Message}");
                return null;
            }
        }

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
                Genres           = genres.ToArray(),
                Watchlist        = ConvertWatchlist(api.Watchlist)
            };
        }

        private static GenreItem[] ConvertWatchlist(List<ApiGenreItem>? items)
        {
            if (items == null) return [];
            var list = new List<GenreItem>();
            foreach (var w in items)
            {
                list.Add(new GenreItem
                {
                    Name        = w.Name ?? "",
                    Score       = w.Score ?? "",
                    TrendLabel  = w.TrendLabel ?? "",
                    Badge       = w.Badge ?? "",
                    ColorHex    = w.ColorHex ?? "#4fc3f7",
                    IsAlternate = w.IsAlternate,
                    BarWidth    = w.BarWidth
                });
            }
            return list.ToArray();
        }
    }

    // Modèle API — snake_case JSON from Python
    public class ApiDomainData
    {
        [System.Text.Json.Serialization.JsonPropertyName("domain")]
        public string? Domain { get; set; }
        [System.Text.Json.Serialization.JsonPropertyName("title")]
        public string? Title { get; set; }
        [System.Text.Json.Serialization.JsonPropertyName("subtitle")]
        public string? Subtitle { get; set; }
        [System.Text.Json.Serialization.JsonPropertyName("kpi_genres")]
        public string? KpiGenres { get; set; }
        [System.Text.Json.Serialization.JsonPropertyName("kpi_score")]
        public string? KpiScore { get; set; }
        [System.Text.Json.Serialization.JsonPropertyName("kpi_opportunities")]
        public string? KpiOpportunities { get; set; }
        [System.Text.Json.Serialization.JsonPropertyName("kpi_precision")]
        public string? KpiPrecision { get; set; }
        [System.Text.Json.Serialization.JsonPropertyName("chart_badge")]
        public string? ChartBadge { get; set; }
        [System.Text.Json.Serialization.JsonPropertyName("bar_color")]
        public string? BarColor { get; set; }
        [System.Text.Json.Serialization.JsonPropertyName("heights")]
        public string? Heights { get; set; }
        [System.Text.Json.Serialization.JsonPropertyName("opportunity_count")]
        public string? OpportunityCount { get; set; }
        [System.Text.Json.Serialization.JsonPropertyName("ia_recommendation")]
        public string? IaRecommendation { get; set; }
        [System.Text.Json.Serialization.JsonPropertyName("genres")]
        public List<ApiGenreItem>? Genres { get; set; }
        [System.Text.Json.Serialization.JsonPropertyName("watchlist")]
        public List<ApiGenreItem>? Watchlist { get; set; }
        [System.Text.Json.Serialization.JsonPropertyName("source")]
        public string? Source { get; set; }
    }

    public class ApiGenreItem
    {
        [System.Text.Json.Serialization.JsonPropertyName("name")]
        public string? Name { get; set; }
        [System.Text.Json.Serialization.JsonPropertyName("score")]
        public string? Score { get; set; }
        [System.Text.Json.Serialization.JsonPropertyName("trend_label")]
        public string? TrendLabel { get; set; }
        [System.Text.Json.Serialization.JsonPropertyName("badge")]
        public string? Badge { get; set; }
        [System.Text.Json.Serialization.JsonPropertyName("color_hex")]
        public string? ColorHex { get; set; }
        [System.Text.Json.Serialization.JsonPropertyName("is_alternate")]
        public bool IsAlternate { get; set; }
        [System.Text.Json.Serialization.JsonPropertyName("bar_width")]
        public double BarWidth { get; set; }
    }
}