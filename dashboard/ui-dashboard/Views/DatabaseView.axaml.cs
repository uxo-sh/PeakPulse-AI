using System;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Media;

namespace ui_dashboard.Views
{
    public partial class DatabaseView : UserControl
    {
        public DatabaseView()
        {
            InitializeComponent();
        }

        protected override void OnLoaded(
            Avalonia.Interactivity.RoutedEventArgs e)
        {
            base.OnLoaded(e);
            _ = LoadDataAsync();
        }

        // Récupère une couleur depuis Themes.axaml
        private IBrush GetThemeBrush(string key)
        {
            if (Application.Current?.TryFindResource(
                    key,
                    Application.Current.ActualThemeVariant,
                    out var res) == true && res is IBrush b)
                return b;
            return Brushes.Transparent;
        }

        private IBrush GetColorBrush(string key)
        {
            return key switch
            {
                "accent"  => GetThemeBrush("AccentBlue"),
                "green"   => new SolidColorBrush(
                    Color.Parse("#4caf50")),
                "purple"  => new SolidColorBrush(
                    Color.Parse("#7c4dff")),
                "orange"  => new SolidColorBrush(
                    Color.Parse("#ff9800")),
                _         => GetThemeBrush("TextPrimary")
            };
        }

        private async Task LoadDataAsync()
        {
            var client = new HttpClient();
            await LoadGamesAsync(client);
            await LoadMoviesAsync(client);
            await LoadTrendsAsync(client);
        }

        private async Task LoadGamesAsync(HttpClient client)
        {
            try
            {
                var json = await client.GetStringAsync(
                    "http://localhost:8000/api/database/games");
                var doc = JsonDocument.Parse(json);
                var data = doc.RootElement.GetProperty("data");

                Avalonia.Threading.Dispatcher.UIThread.Post(() =>
                {
                    var panel = this.FindControl<StackPanel>(
                        "GamesTable");
                    if (panel == null) return;
                    panel.Children.Clear();

                    bool alt = false;
                    foreach (var row in data.EnumerateArray())
                    {
                        panel.Children.Add(BuildGameRow(row, alt));
                        alt = !alt;
                    }
                });
            }
            catch { }
        }

        private async Task LoadMoviesAsync(HttpClient client)
        {
            try
            {
                var json = await client.GetStringAsync(
                    "http://localhost:8000/api/database/movies");
                var doc = JsonDocument.Parse(json);
                var data = doc.RootElement.GetProperty("data");

                Avalonia.Threading.Dispatcher.UIThread.Post(() =>
                {
                    var panel = this.FindControl<StackPanel>(
                        "MoviesTable");
                    if (panel == null) return;
                    panel.Children.Clear();

                    bool alt = false;
                    foreach (var row in data.EnumerateArray())
                    {
                        panel.Children.Add(BuildMovieRow(row, alt));
                        alt = !alt;
                    }
                });
            }
            catch { }
        }

        private async Task LoadTrendsAsync(HttpClient client)
        {
            try
            {
                var json = await client.GetStringAsync(
                    "http://localhost:8000/api/database/trends");
                var doc = JsonDocument.Parse(json);
                var data = doc.RootElement.GetProperty("data");

                Avalonia.Threading.Dispatcher.UIThread.Post(() =>
                {
                    var panel = this.FindControl<StackPanel>(
                        "TrendsTable");
                    if (panel == null) return;
                    panel.Children.Clear();

                    bool alt = false;
                    foreach (var row in data.EnumerateArray())
                    {
                        panel.Children.Add(BuildTrendRow(row, alt));
                        alt = !alt;
                    }
                });
            }
            catch { }
        }

        private Border BuildGameRow(JsonElement row, bool alt)
        {
            var grid = new Grid();
            grid.ColumnDefinitions.Add(
                new ColumnDefinition(80, GridUnitType.Pixel));
            grid.ColumnDefinitions.Add(
                new ColumnDefinition(GridLength.Star));
            grid.ColumnDefinitions.Add(
                new ColumnDefinition(120, GridUnitType.Pixel));
            grid.ColumnDefinitions.Add(
                new ColumnDefinition(100, GridUnitType.Pixel));
            grid.ColumnDefinitions.Add(
                new ColumnDefinition(100, GridUnitType.Pixel));
            grid.ColumnDefinitions.Add(
                new ColumnDefinition(80, GridUnitType.Pixel));

            AddCell(grid, 0,
                row.GetProperty("game_id").ToString(),
                GetColorBrush("accent"));
            AddCell(grid, 1,
                row.GetProperty("title").GetString() ?? "");
            AddCell(grid, 2,
                row.GetProperty("category").GetString() ?? "");
            AddCell(grid, 3,
                row.GetProperty("mechanic").GetString() ?? "");
            AddCell(grid, 4,
                row.GetProperty("players").ToString());
            AddCell(grid, 5,
                row.GetProperty("reviews").ToString(),
                GetColorBrush("green"));

            return WrapRow(grid, alt);
        }

        private Border BuildMovieRow(JsonElement row, bool alt)
        {
            var grid = new Grid();
            grid.ColumnDefinitions.Add(
                new ColumnDefinition(80, GridUnitType.Pixel));
            grid.ColumnDefinitions.Add(
                new ColumnDefinition(GridLength.Star));
            grid.ColumnDefinitions.Add(
                new ColumnDefinition(160, GridUnitType.Pixel));
            grid.ColumnDefinitions.Add(
                new ColumnDefinition(120, GridUnitType.Pixel));
            grid.ColumnDefinitions.Add(
                new ColumnDefinition(80, GridUnitType.Pixel));

            AddCell(grid, 0,
                row.GetProperty("movie_id").ToString(),
                GetColorBrush("purple"));
            AddCell(grid, 1,
                row.GetProperty("title").GetString() ?? "");
            AddCell(grid, 2,
                row.GetProperty("genre").GetString() ?? "");
            AddCell(grid, 3,
                row.GetProperty("views").ToString());
            AddCell(grid, 4,
                row.GetProperty("rating").ToString(),
                GetColorBrush("green"));

            return WrapRow(grid, alt);
        }

        private Border BuildTrendRow(JsonElement row, bool alt)
        {
            var grid = new Grid();
            grid.ColumnDefinitions.Add(
                new ColumnDefinition(GridLength.Star));
            grid.ColumnDefinitions.Add(
                new ColumnDefinition(120, GridUnitType.Pixel));
            grid.ColumnDefinitions.Add(
                new ColumnDefinition(120, GridUnitType.Pixel));

            AddCell(grid, 0,
                row.GetProperty("category").GetString() ?? "");
            AddCell(grid, 1,
                row.GetProperty("trend_score").ToString(),
                GetColorBrush("accent"));

            string pred = row.GetProperty("prediction")
                .GetString() ?? "";
            IBrush predBrush = pred == "hausse"
                ? GetColorBrush("green")
                : pred == "stable"
                    ? GetColorBrush("orange")
                    : GetColorBrush("accent");
            AddCell(grid, 2, pred, predBrush);

            return WrapRow(grid, alt);
        }

        private void AddCell(Grid grid, int col,
            string text, IBrush? brush = null)
        {
            var tb = new TextBlock
            {
                Text = text,
                FontSize = 12,
                Foreground = brush ?? GetThemeBrush("TextPrimary"),
                VerticalAlignment =
                    Avalonia.Layout.VerticalAlignment.Center
            };
            Grid.SetColumn(tb, col);
            grid.Children.Add(tb);
        }

        private Border WrapRow(Grid grid, bool alt)
        {
            return new Border
            {
                Background = alt
                    ? GetThemeBrush("CardBg2")
                    : new SolidColorBrush(Colors.Transparent),
                CornerRadius = new Avalonia.CornerRadius(8),
                Padding = new Avalonia.Thickness(12, 10),
                Child = grid
            };
        }
    }
}