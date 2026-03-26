namespace ui_dashboard.Models
{
    public class GenreItem
    {
        public string Name { get; set; } = "";
        public string Score { get; set; } = "";
        public string TrendLabel { get; set; } = "";
        public string Badge { get; set; } = "";
        public string ColorHex { get; set; } = "#4fc3f7";
        public bool IsAlternate { get; set; }
        public double BarWidth { get; set; }
    }

    public class TrendItem
    {
        public string ItemName { get; set; } = "";
        public string Score { get; set; } = "";
        public string TrendLabel { get; set; } = "";
        public string Badge { get; set; } = "";
        public string ColorHex { get; set; } = "#4fc3f7";
        public bool IsAlternate { get; set; }
    }

    public class DomainData
    {
        public string Title { get; set; } = "";
        public string Subtitle { get; set; } = "";
        public string KpiRecall { get; set; } = "";
        public string KpiPrecision { get; set; } = "";
        public string KpiF1 { get; set; } = "";
        public string KpiAuc { get; set; } = "";
        public string ChartBadge { get; set; } = "";
        public string BarColor { get; set; } = "#4fc3f7";
        public string Heights { get; set; } = "";
        public string IaRecommendation { get; set; } = "";
        public string OpportunityCount { get; set; } = "";
        public TrendItem[] EmergentGenres { get; set; } = System.Array.Empty<TrendItem>();
        public TrendItem[] MeanProbaGenres { get; set; } = System.Array.Empty<TrendItem>();
        public TrendItem[] TrendPercentGenres { get; set; } = System.Array.Empty<TrendItem>();
        public TrendItem[] ExplodingItems { get; set; } = System.Array.Empty<TrendItem>();

        public static DomainData GetEmpty(string domain)
        {
            return new DomainData
            {
                Title = domain == "games" ? "Jeux vidéo — En attente" : "Cinéma — En attente",
                Subtitle = "Cliquez sur Analyser pour démarrer",
                KpiRecall = "0.0%",
                KpiPrecision = "0.0%",
                KpiF1 = "0.0%",
                KpiAuc = "0.0%",
                OpportunityCount = "0",
                IaRecommendation = "Appuyez sur Analyser pour lancer le modèle ML.",
                ChartBadge = "En pause",
                BarColor = "#4fc3f7",
                Heights = "0,0,0,0,0,0"
            };
        }

        public static DomainData Get(string domain)
        {
            return GetEmpty(domain);
        }
    }
}
