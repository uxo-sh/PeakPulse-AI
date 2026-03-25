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

    public class DomainData
    {
        public string Title { get; set; } = "";
        public string Subtitle { get; set; } = "";
        public string KpiGenres { get; set; } = "";
        public string KpiScore { get; set; } = "";
        public string KpiOpportunities { get; set; } = "";
        public string KpiPrecision { get; set; } = "";
        public string ChartBadge { get; set; } = "";
        public string BarColor { get; set; } = "#4fc3f7";
        public string Heights { get; set; } = "";
        public string IaRecommendation { get; set; } = "";
        public string OpportunityCount { get; set; } = "";
        public GenreItem[] Genres { get; set; } = [];
        public GenreItem[] Watchlist { get; set; } = [];

        public static DomainData Get(string domain) => domain switch
        {
            "games" => new DomainData
            {
                Title = "Jeux vidéo — Tendances",
                Subtitle = "Steam · SteamDB · SteamCharts",
                KpiGenres = "87%", KpiScore = "70%",
                KpiOpportunities = "78%", KpiPrecision = "8.4",
                ChartBadge = "Steam · Live",
                BarColor = "#4fc3f7",
                Heights = "0,0,0,0,0,0",
                OpportunityCount = "7 nouvelles",
                IaRecommendation = "Roguelike et Open World en forte hausse sur Steam. Fenêtre optimale : 2 à 6 semaines. Engagement joueur +23% ce mois.",
                Genres = new[]
                {
                    new GenreItem { Name="Roguelike", Score="94%", TrendLabel="↑ En hausse", Badge="Lancer maintenant", ColorHex="#4fc3f7", IsAlternate=true, BarWidth=220 },
                    new GenreItem { Name="Open World", Score="87%", TrendLabel="↑ En hausse", Badge="Lancer maintenant", ColorHex="#7c4dff", IsAlternate=false, BarWidth=200 },
                    new GenreItem { Name="Deckbuilder", Score="79%", TrendLabel="→ Stable", Badge="Surveiller", ColorHex="#ff6b6b", IsAlternate=true, BarWidth=180 },
                    new GenreItem { Name="Survival", Score="71%", TrendLabel="↗ Émergent", Badge="En émergence", ColorHex="#4caf50", IsAlternate=false, BarWidth=160 },
                }
            },
            "movies" => new DomainData
            {
                Title = "Cinéma — Tendances",
                Subtitle = "TMDb · IMDb · Métriques sociales",
                KpiGenres = "72%", KpiScore = "46%",
                KpiOpportunities = "56%", KpiPrecision = "9.4",
                ChartBadge = "TMDb · Live",
                BarColor = "#7c4dff",
                Heights = "0,0,0,0,0,0",
                OpportunityCount = "5 nouvelles",
                IaRecommendation = "Thrillers psychologiques et animation adulte en forte croissance. Fenêtre optimale : 1 à 3 mois.",
                Genres = new[]
                {
                    new GenreItem { Name="Thriller Psycho", Score="91%", TrendLabel="↑ En hausse", Badge="Lancer maintenant", ColorHex="#7c4dff", IsAlternate=true, BarWidth=215 },
                    new GenreItem { Name="Animation Adulte", Score="84%", TrendLabel="↑ En hausse", Badge="Lancer maintenant", ColorHex="#4fc3f7", IsAlternate=false, BarWidth=198 },
                    new GenreItem { Name="Sci-Fi Indie", Score="76%", TrendLabel="→ Stable", Badge="Surveiller", ColorHex="#ff6b6b", IsAlternate=true, BarWidth=178 },
                    new GenreItem { Name="Documentaire", Score="68%", TrendLabel="↗ Émergent", Badge="En émergence", ColorHex="#4caf50", IsAlternate=false, BarWidth=158 },
                }
            },
            _ => new DomainData()
        };
    }
}
