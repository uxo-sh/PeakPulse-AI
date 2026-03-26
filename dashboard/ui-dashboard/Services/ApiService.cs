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
        private static DomainData ConvertToDomainData(ApiDomainData api)
        {
            var emergentGenres = new List<TrendItem>();
            if (api.EmergentGenres != null)
                foreach (var t in api.EmergentGenres) emergentGenres.Add(new TrendItem { ItemName = t.ItemName ?? "", Score = t.Score ?? "", TrendLabel = t.TrendLabel ?? "", Badge = t.Badge ?? "", ColorHex = t.ColorHex ?? "#4fc3f7", IsAlternate = t.IsAlternate });

            var meanProbaGenres = new List<TrendItem>();
            if (api.MeanProbaGenres != null)
                foreach (var t in api.MeanProbaGenres) meanProbaGenres.Add(new TrendItem { ItemName = t.ItemName ?? "", Score = t.Score ?? "", TrendLabel = t.TrendLabel ?? "", Badge = t.Badge ?? "", ColorHex = t.ColorHex ?? "#4fc3f7", IsAlternate = t.IsAlternate });

            var trendPercentGenres = new List<TrendItem>();
            if (api.TrendPercentGenres != null)
                foreach (var t in api.TrendPercentGenres) trendPercentGenres.Add(new TrendItem { ItemName = t.ItemName ?? "", Score = t.Score ?? "", TrendLabel = t.TrendLabel ?? "", Badge = t.Badge ?? "", ColorHex = t.ColorHex ?? "#4fc3f7", IsAlternate = t.IsAlternate });

            var explodingItems = new List<TrendItem>();
            if (api.ExplodingItems != null)
                foreach (var t in api.ExplodingItems) explodingItems.Add(new TrendItem { ItemName = t.ItemName ?? "", Score = t.Score ?? "", TrendLabel = t.TrendLabel ?? "", Badge = t.Badge ?? "", ColorHex = t.ColorHex ?? "#4fc3f7", IsAlternate = t.IsAlternate });

            return new DomainData
            {
                Title            = api.Title ?? "",
                Subtitle         = api.Subtitle ?? "",
                KpiRecall        = api.KpiRecall ?? "",
                KpiPrecision     = api.KpiPrecision ?? "",
                KpiF1            = api.KpiF1 ?? "",
                KpiAuc           = api.KpiAuc ?? "",
                ChartBadge       = api.ChartBadge ?? "",
                BarColor         = api.BarColor ?? "#4fc3f7",
                Heights          = api.Heights ?? "",
                OpportunityCount = api.OpportunityCount ?? "",
                IaRecommendation = api.IaRecommendation ?? "",
                EmergentGenres       = emergentGenres.ToArray(),
                MeanProbaGenres      = meanProbaGenres.ToArray(),
                TrendPercentGenres   = trendPercentGenres.ToArray(),
                ExplodingItems       = explodingItems.ToArray()
            };
        }
    }

    // Modèle API
    public class ApiDomainData
    {
        public string? Domain { get; set; }
        public string? Title { get; set; }
        public string? Subtitle { get; set; }
        public string? KpiRecall { get; set; }
        public string? KpiPrecision { get; set; }
        public string? KpiF1 { get; set; }
        public string? KpiAuc { get; set; }
        public string? ChartBadge { get; set; }
        public string? BarColor { get; set; }
        public string? Heights { get; set; }
        public string? OpportunityCount { get; set; }
        public string? IaRecommendation { get; set; }
        public List<ApiTrendItem>? EmergentGenres { get; set; }
        public List<ApiTrendItem>? MeanProbaGenres { get; set; }
        public List<ApiTrendItem>? TrendPercentGenres { get; set; }
        public List<ApiTrendItem>? ExplodingItems { get; set; }
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

    public class ApiTrendItem
    {
        public string? ItemName { get; set; }
        public string? Score { get; set; }
        public string? TrendLabel { get; set; }
        public string? Badge { get; set; }
        public string? ColorHex { get; set; }
        public bool IsAlternate { get; set; }
    }
}