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

        // =========================
        // THEME
        // =========================

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
                "accent" => GetThemeBrush("AccentBlue"),
                "green" => new SolidColorBrush(Color.Parse("#4caf50")),
                "purple" => new SolidColorBrush(Color.Parse("#7c4dff")),
                "orange" => new SolidColorBrush(Color.Parse("#ff9800")),
                _ => GetThemeBrush("TextPrimary")
            };
        }

        // =========================
        // LOAD DATA
        // =========================

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
                    "http://127.0.0.1:8000/api/database/games");

                var doc = JsonDocument.Parse(json);

                if (!doc.RootElement.TryGetProperty("data", out var data)
                    || data.ValueKind != JsonValueKind.Array)
                {
                    Console.WriteLine("games data invalide");
                    return;
                }

                Avalonia.Threading.Dispatcher.UIThread.Post(() =>
                {
                    var panel = this.FindControl<StackPanel>("GamesTable");
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
            catch (Exception ex)
            {
                Console.WriteLine(" Games error: " + ex.Message);
            }
        }

        private async Task LoadMoviesAsync(HttpClient client)
        {
            try
            {
                var json = await client.GetStringAsync(
                    "http://127.0.0.1:8000/api/database/movies");

                var doc = JsonDocument.Parse(json);

                if (!doc.RootElement.TryGetProperty("data", out var data)
                    || data.ValueKind != JsonValueKind.Array)
                    return;

                Avalonia.Threading.Dispatcher.UIThread.Post(() =>
                {
                    var panel = this.FindControl<StackPanel>("MoviesTable");
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
            catch (Exception ex)
            {
                Console.WriteLine(" Movies error: " + ex.Message);
            }
        }

        private async Task LoadTrendsAsync(HttpClient client)
        {
            try
            {
                var json = await client.GetStringAsync(
                    "http://127.0.0.1:8000/api/database/trends");

                var doc = JsonDocument.Parse(json);

                if (!doc.RootElement.TryGetProperty("data", out var data)
                    || data.ValueKind != JsonValueKind.Array)
                    return;

                Avalonia.Threading.Dispatcher.UIThread.Post(() =>
                {
                    var panel = this.FindControl<StackPanel>("TrendsTable");
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
            catch (Exception ex)
            {
                Console.WriteLine("Trends error: " + ex.Message);
            }
        }

        // =========================
        // SAFE JSON HELPERS
        // =========================

        private string GetString(JsonElement obj, string key)
        {
            return obj.TryGetProperty(key, out var el)
                ? el.ToString()
                : "N/A";
        }

        private int GetInt(JsonElement obj, string key)
        {
            return obj.TryGetProperty(key, out var el)
                && el.ValueKind == JsonValueKind.Number
                ? el.GetInt32()
                : 0;
        }

        private double GetDouble(JsonElement obj, string key)
        {
            return obj.TryGetProperty(key, out var el)
                && el.ValueKind == JsonValueKind.Number
                ? el.GetDouble()
                : 0;
        }

        // =========================
        // ROW BUILDERS
        // =========================

        private Border BuildGameRow(JsonElement row, bool alt)
        {
            var grid = CreateGrid(6);

            AddCell(grid, 0, GetString(row, "game_id"), GetColorBrush("accent"));
            AddCell(grid, 1, GetString(row, "title"));
            AddCell(grid, 2, GetString(row, "category"));
            AddCell(grid, 3, GetString(row, "mechanic"));
            AddCell(grid, 4, GetInt(row, "players").ToString());
            AddCell(grid, 5, GetInt(row, "reviews").ToString(), GetColorBrush("green"));

            return WrapRow(grid, alt);
        }

        private Border BuildMovieRow(JsonElement row, bool alt)
        {
            var grid = CreateGrid(5);

            AddCell(grid, 0, GetString(row, "movie_id"), GetColorBrush("purple"));
            AddCell(grid, 1, GetString(row, "title"));
            AddCell(grid, 2, GetString(row, "genre"));
            AddCell(grid, 3, GetInt(row, "views").ToString());
            AddCell(grid, 4, GetDouble(row, "rating").ToString("0.0"), GetColorBrush("green"));

            return WrapRow(grid, alt);
        }

        private Border BuildTrendRow(JsonElement row, bool alt)
        {
            var grid = CreateGrid(3);

            AddCell(grid, 0, GetString(row, "category"));
            AddCell(grid, 1, GetDouble(row, "trend_score").ToString("0.0"), GetColorBrush("accent"));

            string pred = GetString(row, "prediction");

            IBrush brush = pred switch
            {
                "hausse" => GetColorBrush("green"),
                "stable" => GetColorBrush("orange"),
                _ => GetColorBrush("accent")
            };

            AddCell(grid, 2, pred, brush);

            return WrapRow(grid, alt);
        }

        // =========================
        // UI HELPERS
        // =========================

        private Grid CreateGrid(int columns)
        {
            var grid = new Grid();

            for (int i = 0; i < columns; i++)
                grid.ColumnDefinitions.Add(
                    new ColumnDefinition(GridLength.Star));

            return grid;
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
                    : Brushes.Transparent,
                CornerRadius = new CornerRadius(8),
                Padding = new Thickness(12, 10),
                Child = grid
            };
        }
    }
}