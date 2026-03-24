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
                    "http://127.0.0.1:8000/api/pipeline/status");

                var doc = JsonDocument.Parse(json);

                if (!doc.RootElement.TryGetProperty("steps", out var steps)
                    || steps.ValueKind != JsonValueKind.Array)
                {
                    Console.WriteLine("steps invalide");
                    BuildFallbackPipeline();
                    return;
                }

                Avalonia.Threading.Dispatcher.UIThread.Post(() =>
                {
                    var panel = this.FindControl<StackPanel>("PipelineSteps");
                    if (panel == null) return;

                    panel.Children.Clear();

                    foreach (var step in steps.EnumerateArray())
                    {
                        int num = GetInt(step, "step");
                        string name = GetString(step, "name");
                        string status = GetString(step, "status");

                        string detail = "";

                        if (step.TryGetProperty("source", out var src))
                            detail = src.ToString();

                        else if (step.TryGetProperty("model", out var mdl)
                            && step.TryGetProperty("accuracy", out var acc))
                            detail = $"{mdl} — {GetDouble(acc):P0}";

                        else if (step.TryGetProperty("port", out var port))
                            detail = $"Port {port}";

                        else if (step.TryGetProperty("records", out var rec))
                            detail = $"{rec} records";

                        string extra = "";

                        extra = ParseArray(step, "examples", e =>
                            $"{GetString(e, "tag")} → {GetString(e, "category")}");

                        if (string.IsNullOrEmpty(extra))
                            extra = ParseArray(step, "algorithms", e => e.ToString());

                        if (string.IsNullOrEmpty(extra))
                            extra = ParseArray(step, "features", e => e.ToString());

                        if (string.IsNullOrEmpty(extra))
                            extra = ParseArray(step, "endpoints", e => e.ToString());

                        panel.Children.Add(
                            BuildStepCard(num, name, status, detail, extra));
                    }
                });
            }
            catch (Exception ex)
            {
                Console.WriteLine(" ERROR: " + ex.Message);
                BuildFallbackPipeline();
            }
        }

        // =========================
        //  SAFE JSON HELPERS
        // =========================

        private int GetInt(JsonElement obj, string key)
        {
            return obj.TryGetProperty(key, out var el) && el.ValueKind == JsonValueKind.Number
                ? el.GetInt32()
                : 0;
        }

        private double GetDouble(JsonElement el)
        {
            return el.ValueKind == JsonValueKind.Number
                ? el.GetDouble()
                : 0;
        }

        private string GetString(JsonElement obj, string key)
        {
            return obj.TryGetProperty(key, out var el)
                ? el.ToString()
                : "";
        }

        private string ParseArray(JsonElement parent, string key,
            Func<JsonElement, string> selector)
        {
            if (!parent.TryGetProperty(key, out var element))
                return "";

            if (element.ValueKind != JsonValueKind.Array)
            {
                Console.WriteLine($"{key} n'est pas un tableau !");
                return element.ToString();
            }

            var list = new List<string>();

            foreach (var item in element.EnumerateArray())
            {
                try
                {
                    list.Add(selector(item));
                }
                catch
                {
                    list.Add(item.ToString());
                }
            }

            return string.Join(" · ", list);
        }

        // =========================
        // UI
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

        private Border BuildStepCard(int num, string name,
            string status, string detail, string extra = "")
        {
            var isOk = status == "ok";

            var numBorder = new Border
            {
                Width = 36,
                Height = 36,
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
                Width = 18,
                Height = 18,
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
                    TextWrapping = TextWrapping.Wrap
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

        // =========================
        // FALLBACK
        // =========================

        private void BuildFallbackPipeline()
        {
            Console.WriteLine("fallback pipeline utilisé");

            var steps = new[]
            {
                (1, "Collecte données", "ok", "Steam + TMDb", "tags · joueurs"),
                (2, "Nettoyage", "ok", "15k records", "drop_duplicates"),
                (3, "ML", "ok", "RandomForest — 92%", "prediction"),
                (4, "API", "ok", "Port 8000", "GET endpoints")
            };

            Avalonia.Threading.Dispatcher.UIThread.Post(() =>
            {
                var panel = this.FindControl<StackPanel>("PipelineSteps");
                if (panel == null) return;

                panel.Children.Clear();

                foreach (var s in steps)
                    panel.Children.Add(
                        BuildStepCard(s.Item1, s.Item2, s.Item3, s.Item4, s.Item5));
            });
        }
    }
}