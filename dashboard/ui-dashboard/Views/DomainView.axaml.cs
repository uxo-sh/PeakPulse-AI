using System;
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
            LoadData();
            var searchBox = this.FindControl<TextBox>("SearchBox");
            if (searchBox != null)
                searchBox.TextChanged += OnSearchChanged;
        }

        private async void LoadData()
        {
            var apiData = await Services.ApiService.Instance
                .GetTrendsAsync(_domain);
            var data = apiData ?? DomainData.Get(_domain);
            UpdateUIWithData(data);
        }

        private void UpdateUIWithData(DomainData data)
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
                    "games"  => MaterialIconKind.Gamepad,
                    "movies" => MaterialIconKind.Movie,
                    "music"  => MaterialIconKind.Music,
                    _        => MaterialIconKind.TrendingUp
                };
            });

            Set<KpiCard>("KpiGenres",
                k => k.Value = data.KpiGenres);
            Set<KpiCard>("KpiScore",
                k => k.Value = data.KpiScore);
            Set<KpiCard>("KpiOpportunities",
                k => k.Value = data.KpiOpportunities);
            Set<KpiCard>("KpiPrecision",
                k => k.Value = data.KpiPrecision);

            Set<LineChart>("MainLineChart", c =>
            {
                c.DataPoints = "0,0,0,0,0,0";
                c.Badge      = data.ChartBadge;
                c.ColorHex   = data.BarColor;
                c.Title      = "Évolution (Données Statiques)";
            });

            Set<BarChart>("MainChart", c =>
            {
                c.Title    = "Distribution (Données Statiques)";
                c.Badge    = data.ChartBadge;
                c.BarColor = data.BarColor;
                c.Heights  = "0,0,0,0,0,0";
            });

            Set<TextBlock>("OpportunityBadge",
                t => t.Text = data.OpportunityCount);
            Set<TextBlock>("IaTitle",
                t => t.Text =
                    $"Recommandation IA — {data.Title}");
            Set<TextBlock>("IaText",
                t => t.Text = data.IaRecommendation);

            BuildTopGenres(data);
            BuildTrendRows(data);
            BuildWatchlistRows(data);
        }

        private void OnSearchChanged(object? sender,
            TextChangedEventArgs e)
        {
            var searchBox = sender as TextBox;
            var query = searchBox?.Text?.ToLower() ?? "";

            var panel = this.FindControl<StackPanel>(
                "TrendRowsPanel");
            if (panel == null) return;

            foreach (var child in panel.Children)
            {
                if (child is not Controls.TrendRow row) continue;
                row.IsVisible = string.IsNullOrWhiteSpace(query)
                    || row.ItemName.ToLower().Contains(query)
                    || row.TrendLabel.ToLower().Contains(query)
                    || row.Badge.ToLower().Contains(query);
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
            var searchBox = this.FindControl<TextBox>("SearchBox");
            var query = searchBox?.Text ?? "";

            if (string.IsNullOrWhiteSpace(query))
            {
                ShowNotification(
                    "Analyse complète en cours... (ML Pipeline)",
                    "#7c4dff");

                var data = await Services.ApiService.Instance.AnalyzeAsync(_domain);
                if (data != null)
                {
                    Avalonia.Threading.Dispatcher.UIThread.Post(() =>
                    {
                        UpdateUIWithData(data);
                        ShowNotification("✅ Analyse terminée avec succès", "#4caf50");
                    });
                }
                else
                {
                    Avalonia.Threading.Dispatcher.UIThread.Post(() =>
                    {
                        ShowNotification("⚠️ Erreur lors de l'analyse ML", "#ff9800");
                    });
                }
                return;
            }

            ShowNotification(
                $"Analyse de '{query}' en cours...",
                "#4fc3f7");

            _ = AnalyzeQueryAsync(query);
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

        private void BuildTopGenres(DomainData data)
        {
            var panel = this.FindControl<StackPanel>(
                "TopGenresPanel");
            if (panel == null) return;
            panel.Children.Clear();

            foreach (var g in data.Genres)
            {
                var sp = new StackPanel
                {
                    Margin = new Avalonia.Thickness(0, 0, 0, 16)
                };

                var grid = new Grid();
                grid.ColumnDefinitions.Add(
                    new ColumnDefinition(GridLength.Star));
                grid.ColumnDefinitions.Add(
                    new ColumnDefinition(GridLength.Auto));
                grid.Margin = new Avalonia.Thickness(0, 0, 0, 6);

                var nameText = new TextBlock
                {
                    Text = g.Name,
                    Foreground = new SolidColorBrush(
                        Avalonia.Media.Colors.White),
                    FontSize = 12
                };
                var scoreText = new TextBlock
                {
                    Text = g.Score,
                    Foreground = new SolidColorBrush(
                        Avalonia.Media.Color.Parse(g.ColorHex)),
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
                    Background = new SolidColorBrush(
                        Avalonia.Media.Color.Parse("#1e2d40")),
                    CornerRadius = new Avalonia.CornerRadius(2)
                };
                var fill = new Border
                {
                    Width = g.BarWidth,
                    Height = 4,
                    Background = new SolidColorBrush(
                        Avalonia.Media.Color.Parse(g.ColorHex)),
                    CornerRadius = new Avalonia.CornerRadius(2),
                    HorizontalAlignment =
                        Avalonia.Layout.HorizontalAlignment.Left
                };
                track.Child = fill;

                sp.Children.Add(grid);
                sp.Children.Add(track);
                panel.Children.Add(sp);
            }
        }

        private void BuildTrendRows(DomainData data)
        {
            var panel = this.FindControl<StackPanel>(
                "TrendRowsPanel");
            if (panel == null) return;
            panel.Children.Clear();

            foreach (var g in data.Genres)
            {
                var row = new TrendRow
                {
                    ItemName    = g.Name,
                    Score       = g.Score,
                    TrendLabel  = g.TrendLabel,
                    Badge       = g.Badge,
                    ColorHex    = g.ColorHex,
                    IsAlternate = g.IsAlternate
                };
                panel.Children.Add(row);
            }
        }

        private void BuildWatchlistRows(DomainData data)
        {
            var section = this.FindControl<Border>("WatchlistSection");
            var panel = this.FindControl<StackPanel>("WatchlistRowsPanel");
            if (panel == null) return;
            panel.Children.Clear();

            if (data.Watchlist == null || data.Watchlist.Length == 0)
            {
                if (section != null) section.IsVisible = false;
                return;
            }

            if (section != null) section.IsVisible = true;

            // Dynamic title based on domain
            Set<TextBlock>("WatchlistTitle", t =>
                t.Text = _domain == "movies"
                    ? "\U0001f525 Films qui vont exploser"
                    : "\U0001f525 Jeux qui vont exploser");
            Set<TextBlock>("WatchlistBadge", t =>
                t.Text = $"{data.Watchlist.Length} détectés");

            foreach (var w in data.Watchlist)
            {
                var row = new TrendRow
                {
                    ItemName    = w.Name,
                    Score       = w.Score,
                    TrendLabel  = w.TrendLabel,
                    Badge       = w.Badge,
                    ColorHex    = w.ColorHex,
                    IsAlternate = w.IsAlternate
                };
                panel.Children.Add(row);
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