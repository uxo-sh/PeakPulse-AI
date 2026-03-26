using System;
using System.Linq;
using System.Threading.Tasks;
using Avalonia.Controls;
using Avalonia.Media;
using Material.Icons;
using Material.Icons.Avalonia;
using ui_dashboard.Controls;
using ui_dashboard.Models;

namespace ui_dashboard.Views
{
    public partial class DomainView : UserControl
    {
        private readonly string _domain;
        public string Domain => _domain;

        public DomainView() : this("games") { }

        public DomainView(string domain)
        {
            _domain = domain;
            InitializeComponent();
        }

        protected override void OnLoaded(
            Avalonia.Interactivity.RoutedEventArgs e)
        {
            base.OnLoaded(e);
            // Charger les données initialement à 0
            var emptyData = DomainData.GetEmpty(_domain);
            LoadData(emptyData);
            var searchBox = this.FindControl<TextBox>("SearchBox");
            if (searchBox != null)
                searchBox.TextChanged += OnSearchChanged;
        }

        private void LoadData(DomainData data)
        {
            Set<TextBlock>("TitleText",
                t => t.Text = data.Title);
            Set<TextBlock>("SubtitleText",
                t => t.Text = data.Subtitle);
            Set<TextBlock>("DateText",
                t => t.Text = DateTime.Now
                    .ToString("dd MMMM yyyy"));

            Set<MaterialIcon>("DomainIcon", i =>
            {
                i.Kind = _domain switch
                {
                    "games" => MaterialIconKind.Gamepad,
                    "movies" => MaterialIconKind.Movie,
                    "music" => MaterialIconKind.Music,
                    _ => MaterialIconKind.TrendingUp
                };
            });

            Set<KpiCard>("KpiRecall",
                k => k.Value = data.KpiRecall);
            Set<KpiCard>("KpiF1",
                k => k.Value = data.KpiF1);
            Set<KpiCard>("KpiAuc",
                k => k.Value = data.KpiAuc);
            Set<KpiCard>("KpiPrecision",
                k => k.Value = data.KpiPrecision);

            Set<LineChart>("MainLineChart", c =>
            {
                c.DataPoints = data.Heights;
                c.Badge = data.ChartBadge;
                c.ColorHex = data.BarColor;
                c.Title = "Évolution — 6 derniers mois";
            });

            Set<CircleBar>("CircleScore", c =>
            {
                c.Value = double.TryParse(
                    data.KpiF1.Replace("%", ""),
                    out var v) ? v : 0;
                c.ColorHex = "#4fc3f7";
            });

            Set<CircleBar>("CirclePrecision", c =>
            {
                c.Value = double.TryParse(
                    data.KpiPrecision,
                    out var v) ? v * 10 : 0;
                c.ColorHex = "#4caf50";
            });

            Set<CircleBar>("CircleOpportunity", c =>
            {
                c.Value = double.TryParse(
                    data.KpiAuc,
                    out var v) ? v * 10 : 0;
                c.ColorHex = "#ff6b6b";
            });

            Set<BarChart>("MainChart", c =>
            {
                c.Title = "Évolution — 6 derniers mois";
                c.Badge = data.ChartBadge;
                c.BarColor = data.BarColor;
                c.Heights = data.Heights;
            });

            Set<TextBlock>("OpportunityBadge",
                t => t.Text = data.OpportunityCount);
            Set<TextBlock>("IaTitle",
                t => t.Text =
                    $"Recommandation IA — {data.Title}");
            Set<TextBlock>("IaText",
                t => t.Text = data.IaRecommendation);

            Set<TextBlock>("Header1", t => t.Text = _domain == "games" ? "Proba" : "Score");
            Set<TextBlock>("Header2", t => t.Text = _domain == "games" ? "Genre" : "Proba");
            Set<TextBlock>("Header3", t => t.Text = _domain == "games" ? "Prix" : "Budget");

            BuildPanel("EmergentGenresPanel", data.EmergentGenres);
            BuildPanel("MeanProbaGenresPanel", data.MeanProbaGenres);
            BuildPanel("TrendPercentGenresPanel", data.TrendPercentGenres);
            BuildPanel("ExplodingItemsPanel", data.ExplodingItems);
            BuildTopGenres(data.EmergentGenres);
        }

        private void OnSearchChanged(object? sender,
            TextChangedEventArgs e)
        {
            var searchBox = sender as TextBox;
            var query = searchBox?.Text?.ToLower() ?? "";

            var panels = new[] {
                this.FindControl<StackPanel>("EmergentGenresPanel"),
                this.FindControl<StackPanel>("MeanProbaGenresPanel"),
                this.FindControl<StackPanel>("TrendPercentGenresPanel"),
                this.FindControl<StackPanel>("ExplodingItemsPanel")
            };

            foreach (var panel in panels)
            {
                if (panel == null) continue;
                foreach (var child in panel.Children)
                {
                    if (child is not Controls.TrendRow row) continue;
                    row.IsVisible = string.IsNullOrWhiteSpace(query)
                        || row.ItemName.ToLower().Contains(query)
                        || row.TrendLabel.ToLower().Contains(query)
                        || row.Badge.ToLower().Contains(query);
                }
            }
        }

        private void OnSearchKeyDown(object? sender,
            Avalonia.Input.KeyEventArgs e)
        {
            if (e.Key == Avalonia.Input.Key.Enter)
            {
                var searchBox = sender as TextBox;
                var query = searchBox?.Text ?? "";
                if (!string.IsNullOrWhiteSpace(query))
                {
                    ShowNotification(
                        $"Analyse de '{query}' en cours...",
                        "#4fc3f7");
                    _ = AnalyzeQueryAsync(query);
                }
            }
        }

        private async void OnImportClick(object? sender,
            Avalonia.Interactivity.RoutedEventArgs e)
        {
            var dialog = new Avalonia.Platform.Storage
                .FilePickerOpenOptions
            {
                Title = "Importer un fichier de données",
                AllowMultiple = false,
                FileTypeFilter = new[]
                {
                    new Avalonia.Platform.Storage
                        .FilePickerFileType("CSV")
                    {
                        Patterns = new[] { "*.csv" }
                    },
                    new Avalonia.Platform.Storage
                        .FilePickerFileType("JSON")
                    {
                        Patterns = new[] { "*.json" }
                    },
                    new Avalonia.Platform.Storage
                        .FilePickerFileType("Tous les fichiers")
                    {
                        Patterns = new[] { "*.*" }
                    }
                }
            };

            var window = TopLevel.GetTopLevel(this);
            if (window == null) return;

            var files = await window.StorageProvider
                .OpenFilePickerAsync(dialog);

            if (files.Count > 0)
            {
                var file = files[0];
                ShowNotification(
                    $"Fichier importé : {file.Name}",
                    "#4caf50");
            }
        }

        private async void OnAnalyzeClick(object? sender,
            Avalonia.Interactivity.RoutedEventArgs e)
        {
            var btn = sender as Button;
            var txt = this.FindControl<TextBlock>("BtnAnalyzeText");
            if (btn != null) btn.IsEnabled = false;
            if (txt != null) txt.Text = "En cours...";

            // Chargement ML en direct (3 secondes)
            await System.Threading.Tasks.Task.Delay(3000);

            var data = await Services.ApiService.Instance
                .GetTrendsAsync(_domain);
            if (data != null)
            {
                LoadData(data);
            }

            if (btn != null) btn.IsEnabled = true;
            if (txt != null) txt.Text = "Analyser";
        }

        private async Task AnalyzeQueryAsync(string query)
        {
            try
            {
                var client = new System.Net.Http.HttpClient();
                var json = await client.GetStringAsync(
                    $"http://localhost:8000/api/genre_prediction/{query}");
                var doc = System.Text.Json.JsonDocument.Parse(json);
                var prob = doc.RootElement
                    .GetProperty("success_probability")
                    .GetDouble();
                var reco = doc.RootElement
                    .GetProperty("recommendation")
                    .GetString() ?? "";

                Avalonia.Threading.Dispatcher.UIThread.Post(() =>
                {
                    ShowNotification(
                        $"  '{query}' — Score : {prob:P0} — {reco}",
                        "#4caf50");
                });
            }
            catch
            {
                Avalonia.Threading.Dispatcher.UIThread.Post(() =>
                {
                    ShowNotification(
                        "⚠️ API non disponible — données simulées",
                        "#ff9800");
                });
            }
        }

        //   ShowNotification avec timer 4 secondes
        private void ShowNotification(string message,
            string colorHex)
        {
            Avalonia.Threading.Dispatcher.UIThread.Post(() =>
            {
                var panel = this.FindControl<StackPanel>(
                    "NotificationPanel");
                if (panel == null) return;

                panel.Children.Clear();

                var color = Avalonia.Media.Color.Parse(colorHex);
                var notif = new Border
                {
                    Background = new SolidColorBrush(
                        Avalonia.Media.Color.FromArgb(
                            40, color.R, color.G, color.B)),
                    BorderBrush = new SolidColorBrush(color),
                    BorderThickness = new Avalonia.Thickness(1),
                    CornerRadius = new Avalonia.CornerRadius(8),
                    Padding = new Avalonia.Thickness(16, 12),
                    Margin = new Avalonia.Thickness(0, 0, 0, 16),
                    Child = new TextBlock
                    {
                        Text = message,
                        Foreground = new SolidColorBrush(color),
                        FontSize = 13,
                        FontWeight = FontWeight.Bold
                    }
                };
                panel.Children.Add(notif);

                // Efface après 4 secondes
                _ = Task.Delay(4000).ContinueWith(_ =>
                {
                    Avalonia.Threading.Dispatcher.UIThread.Post(
                        () => panel.Children.Clear());
                });
            });
        }

        private void BuildPanel(string panelName, TrendItem[]? items)
        {
            var panel = this.FindControl<StackPanel>(panelName);
            if (panel == null) return;
            panel.Children.Clear();
            if (items == null) return;

            foreach (var t in items)
            {
                var row = new Controls.TrendRow
                {
                    ItemName = t.ItemName,
                    Score = t.Score,
                    TrendLabel = t.TrendLabel,
                    Badge = t.Badge,
                    ColorHex = t.ColorHex,
                    IsAlternate = t.IsAlternate
                };
                panel.Children.Add(row);
            }
        }

        private void BuildTopGenres(TrendItem[]? items)
        {
            var panel = this.FindControl<StackPanel>("TopGenresPanel");
            if (panel == null) return;
            panel.Children.Clear();
            if (items == null || items.Length == 0) return;

            // Afficher max 4 genres dans le panneau latéral
            foreach (var g in items.Take(4))
            {
                double ratio = 0;
                if (double.TryParse(g.TrendLabel?.Replace("%", ""), out var r))
                    ratio = r;
                int barW = 50 + (int)(ratio * 1.5);

                var sp = new StackPanel { Margin = new Avalonia.Thickness(0, 0, 0, 16) };
                var grid = new Grid();
                grid.ColumnDefinitions.Add(new ColumnDefinition(GridLength.Star));
                grid.ColumnDefinitions.Add(new ColumnDefinition(GridLength.Auto));
                grid.Margin = new Avalonia.Thickness(0, 0, 0, 6);

                var nameText = new TextBlock
                {
                    Text = g.ItemName,
                    Foreground = new SolidColorBrush(Avalonia.Media.Colors.White),
                    FontSize = 12
                };
                var scoreText = new TextBlock
                {
                    Text = g.Score,
                    Foreground = new SolidColorBrush(Avalonia.Media.Color.Parse(g.ColorHex)),
                    FontSize = 12,
                    FontWeight = FontWeight.Bold
                };
                Grid.SetColumn(nameText, 0);
                Grid.SetColumn(scoreText, 1);
                grid.Children.Add(nameText);
                grid.Children.Add(scoreText);

                var track = new Border
                {
                    Height = 4,
                    Background = new SolidColorBrush(Avalonia.Media.Color.Parse("#1e2d40")),
                    CornerRadius = new Avalonia.CornerRadius(2)
                };
                var fill = new Border
                {
                    Width = barW,
                    Height = 4,
                    Background = new SolidColorBrush(Avalonia.Media.Color.Parse(g.ColorHex)),
                    CornerRadius = new Avalonia.CornerRadius(2),
                    HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Left
                };
                track.Child = fill;

                sp.Children.Add(grid);
                sp.Children.Add(track);
                panel.Children.Add(sp);
            }
        }

        private void Set<T>(string name, Action<T> action)
            where T : Control
        {
            if (this.FindControl<T>(name) is T ctrl)
                action(ctrl);
        }
    }
}