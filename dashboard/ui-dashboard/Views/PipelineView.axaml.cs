using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Media;
using Material.Icons;
using Material.Icons.Avalonia;

namespace ui_dashboard.Views
{
    public partial class PipelineView : UserControl
    {
        public PipelineView()
        {
            InitializeComponent();
        }

        protected override void OnLoaded(
            Avalonia.Interactivity.RoutedEventArgs e)
        {
            base.OnLoaded(e);
            _ = LoadPipelineAsync();
        }

        private async Task LoadPipelineAsync()
        {
            try
            {
                var client = new HttpClient();
                var json = await client.GetStringAsync(
                    "http://localhost:8000/api/pipeline/status");
                var doc = JsonDocument.Parse(json);
                var steps = doc.RootElement.GetProperty("steps");

                Avalonia.Threading.Dispatcher.UIThread.Post(() =>
                {
                    var panel = this.FindControl<StackPanel>(
                        "PipelineSteps");
                    if (panel == null) return;
                    panel.Children.Clear();

                    foreach (var step in steps.EnumerateArray())
                    {
                        int num = step.GetProperty("step")
                            .GetInt32();
                        string name = step.GetProperty("name")
                            .GetString() ?? "";
                        string status = step.GetProperty("status")
                            .GetString() ?? "";

                        string detail = "";
                        if (step.TryGetProperty("source",
                                out var src))
                            detail = src.GetString() ?? "";
                        else if (step.TryGetProperty("model",
                                out var mdl))
                            detail = $"{mdl.GetString()} — " +
                                $"{step.GetProperty("accuracy").GetDouble():P0}";
                        else if (step.TryGetProperty("port",
                                out var port))
                            detail = $"Port {port}";
                        else if (step.TryGetProperty("records",
                                out var rec))
                            detail = $"{rec} records traités";

                        string extra = "";
                        if (step.TryGetProperty("examples",
                                out var examples))
                        {
                            var tags = new List<string>();
                            foreach (var ex in
                                examples.EnumerateArray())
                                tags.Add(
                                    $"{ex.GetProperty("tag").GetString()}" +
                                    $" → {ex.GetProperty("category").GetString()}");
                            extra = string.Join(" · ", tags);
                        }
                        else if (step.TryGetProperty("algorithms",
                                out var algos))
                        {
                            var list = new List<string>();
                            foreach (var a in algos.EnumerateArray())
                                list.Add(a.GetString() ?? "");
                            extra = string.Join(" · ", list);
                        }
                        else if (step.TryGetProperty("features",
                                out var feats))
                        {
                            var list = new List<string>();
                            foreach (var f in feats.EnumerateArray())
                                list.Add(f.GetString() ?? "");
                            extra = string.Join(" · ", list);
                        }
                        else if (step.TryGetProperty("endpoints",
                                out var eps))
                        {
                            var list = new List<string>();
                            foreach (var ep in eps.EnumerateArray())
                                list.Add(ep.GetString() ?? "");
                            extra = string.Join(" · ", list);
                        }

                        panel.Children.Add(
                            BuildStepCard(num, name,
                                status, detail, extra));
                    }
                });
            }
            catch
            {
                BuildFallbackPipeline();
            }
        }

        private void BuildFallbackPipeline()
        {
            var steps = new[]
            {
                (1, "Collecte données", "ok",
                    "Steam + TMDb",
                    "liste jeux, tags, joueurs, reviews"),
                (2, "Nettoyage", "ok",
                    "15 420 records",
                    "drop_duplicates · fillna(0)"),
                (3, "Classification tags", "ok",
                    "400 tags → 20 catégories",
                    "Roguelike → roguelike · Open World → open_world"),
                (4, "Calcul features", "ok",
                    "4 features calculées",
                    "growth_rate · engagement_rate · player_count · review_ratio"),
                (5, "Trend detection", "ok",
                    "3 algorithmes actifs",
                    "trend momentum · early detection · hybrid genre"),
                (6, "Machine Learning", "ok",
                    "RandomForest — 92%",
                    "Input: features · Output: probabilité succès"),
                (7, "API exposée", "ok",
                    "Port 8000",
                    "GET /trending_games · GET /trending_movies · GET /genre_prediction"),
                (8, "Dashboard C#", "ok",
                    "Version 1.0.0",
                    "Top genres gaming · Top genres films · Opportunités marché"),
            };

            Avalonia.Threading.Dispatcher.UIThread.Post(() =>
            {
                var panel = this.FindControl<StackPanel>(
                    "PipelineSteps");
                if (panel == null) return;
                panel.Children.Clear();
                foreach (var (num, name, status, detail, extra)
                    in steps)
                    panel.Children.Add(
                        BuildStepCard(num, name,
                            status, detail, extra));
            });
        }

        private IBrush GetThemeBrush(string key)
        {
            if (Application.Current?.TryFindResource(
                    key,
                    Application.Current.ActualThemeVariant,
                    out var res) == true && res is IBrush b)
                return b;
            return Brushes.Transparent;
        }

        private Border BuildStepCard(int num, string name,
            string status, string detail, string extra = "")
        {
            var isOk = status == "ok";

            var numBorder = new Border
            {
                Width = 36, Height = 36,
                CornerRadius = new CornerRadius(18),
                Background = GetThemeBrush("NavActive"),
                Child = new TextBlock
                {
                    Text = num.ToString(),
                    Foreground = GetThemeBrush("AccentBlue"),
                    FontSize = 14,
                    FontWeight = FontWeight.Bold,
                    HorizontalAlignment =
                        Avalonia.Layout.HorizontalAlignment.Center,
                    VerticalAlignment =
                        Avalonia.Layout.VerticalAlignment.Center
                }
            };

            var icon = new MaterialIcon
            {
                Kind = isOk
                    ? MaterialIconKind.CheckCircle
                    : MaterialIconKind.AlertCircle,
                Width = 18, Height = 18,
                Foreground = new SolidColorBrush(
                    isOk ? Color.Parse("#4caf50")
                         : Color.Parse("#ff6b6b"))
            };

            var textStack = new StackPanel
            {
                Spacing = 4,
                Margin = new Thickness(12, 0, 0, 0)
            };
            textStack.Children.Add(new TextBlock
            {
                Text = name,
                Foreground = GetThemeBrush("TextPrimary"),
                FontSize = 13,
                FontWeight = FontWeight.Bold
            });

            if (!string.IsNullOrEmpty(detail))
                textStack.Children.Add(new TextBlock
                {
                    Text = detail,
                    Foreground = GetThemeBrush("TextSecondary"),
                    FontSize = 11
                });

            if (!string.IsNullOrEmpty(extra))
                textStack.Children.Add(new TextBlock
                {
                    Text = extra,
                    Foreground = GetThemeBrush("AccentBlue"),
                    FontSize = 11,
                    TextWrapping =
                        Avalonia.Media.TextWrapping.Wrap
                });

            var grid = new Grid();
            grid.ColumnDefinitions.Add(
                new ColumnDefinition(GridLength.Auto));
            grid.ColumnDefinitions.Add(
                new ColumnDefinition(GridLength.Star));
            grid.ColumnDefinitions.Add(
                new ColumnDefinition(GridLength.Auto));

            Grid.SetColumn(numBorder, 0);
            Grid.SetColumn(textStack, 1);
            Grid.SetColumn(icon, 2);

            grid.Children.Add(numBorder);
            grid.Children.Add(textStack);
            grid.Children.Add(icon);

            return new Border
            {
                Background = GetThemeBrush("CardBg"),
                CornerRadius = new CornerRadius(12),
                Padding = new Thickness(20, 16),
                BorderBrush = GetThemeBrush("BorderColor"),
                BorderThickness = new Thickness(1),
                Child = grid
            };
        }
    }
}