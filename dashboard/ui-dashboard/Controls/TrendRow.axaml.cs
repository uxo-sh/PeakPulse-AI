using Avalonia;
using Avalonia.Controls;
using Avalonia.Media;

namespace ui_dashboard.Controls
{
    public partial class TrendRow : UserControl
    {
        public static readonly StyledProperty<string> ItemNameProperty =
            AvaloniaProperty.Register<TrendRow, string>(nameof(ItemName));
        public static readonly StyledProperty<string> ScoreProperty =
            AvaloniaProperty.Register<TrendRow, string>(nameof(Score));
        public static readonly StyledProperty<string> TrendLabelProperty =
            AvaloniaProperty.Register<TrendRow, string>(nameof(TrendLabel));
        public static readonly StyledProperty<string> BadgeProperty =
            AvaloniaProperty.Register<TrendRow, string>(nameof(Badge));
        public static readonly StyledProperty<string> ColorHexProperty =
            AvaloniaProperty.Register<TrendRow, string>(nameof(ColorHex), "#4fc3f7");
        public static readonly StyledProperty<bool> IsAlternateProperty =
            AvaloniaProperty.Register<TrendRow, bool>(nameof(IsAlternate), false);

        public string ItemName
        {
            get => GetValue(ItemNameProperty);
            set => SetValue(ItemNameProperty, value);
        }
        public string Score
        {
            get => GetValue(ScoreProperty);
            set => SetValue(ScoreProperty, value);
        }
        public string TrendLabel
        {
            get => GetValue(TrendLabelProperty);
            set => SetValue(TrendLabelProperty, value);
        }
        public string Badge
        {
            get => GetValue(BadgeProperty);
            set => SetValue(BadgeProperty, value);
        }
        public string ColorHex
        {
            get => GetValue(ColorHexProperty);
            set => SetValue(ColorHexProperty, value);
        }
        public bool IsAlternate
        {
            get => GetValue(IsAlternateProperty);
            set => SetValue(IsAlternateProperty, value);
        }

        public TrendRow()
        {
            InitializeComponent();
        }

        protected override void OnLoaded(
            Avalonia.Interactivity.RoutedEventArgs e)
        {
            base.OnLoaded(e);
            UpdateUI();
        }

        private IBrush GetBrush(string key)
        {
            var theme = Application.Current?.ActualThemeVariant
                ?? Avalonia.Styling.ThemeVariant.Dark;

            if (Application.Current?.TryFindResource(
                    key, theme, out var res) == true
                && res is IBrush b)
                return b;

            return key switch
            {
                "BadgeGreenBg" => new SolidColorBrush(
                    Color.Parse("#1a3a1a")),
                "BadgeGreenFg" => new SolidColorBrush(
                    Color.Parse("#4caf50")),
                "BadgeOrangeBg" => new SolidColorBrush(
                    Color.Parse("#3a2a1a")),
                "BadgeOrangeFg" => new SolidColorBrush(
                    Color.Parse("#ff9800")),
                "BadgeBlueBg" => new SolidColorBrush(
                    Color.Parse("#1a2744")),
                "BadgeBlueFg" => new SolidColorBrush(
                    Color.Parse("#4fc3f7")),
                _ => new SolidColorBrush(Colors.Transparent)
            };
        }

        private void UpdateUI()
        {
            var color = Color.Parse(ColorHex);
            var brush = new SolidColorBrush(color);

            if (this.FindControl<Border>("RowBorder") is Border row)
                row.Background = IsAlternate
                    ? new SolidColorBrush(
                        Color.FromArgb(40, 100, 120, 150))
                    : new SolidColorBrush(Colors.Transparent);

            if (this.FindControl<Border>("DotColor") is Border dot)
                dot.Background = brush;

            if (this.FindControl<TextBlock>("NameText")
                    is TextBlock name)
                name.Text = ItemName;

            if (this.FindControl<TextBlock>("ScoreText")
                    is TextBlock score)
            {
                score.Text = Score;
                score.Foreground = brush;
            }

            if (this.FindControl<TextBlock>("TrendText")
                    is TextBlock trend)
            {
                trend.Text = TrendLabel;
                trend.Foreground = TrendLabel.Contains("hausse")
                    ? new SolidColorBrush(Color.Parse("#4caf50"))
                    : TrendLabel.Contains("Stable")
                        ? new SolidColorBrush(Color.Parse("#ff9800"))
                        : new SolidColorBrush(Color.Parse("#4fc3f7"));
            }

            if (this.FindControl<Border>("BadgeBorder") is Border badge
                && this.FindControl<TextBlock>("BadgeText") is TextBlock badgeTxt
                && this.FindControl<StackPanel>("IconsPanel") is StackPanel iconsPanel)
            {
                iconsPanel.Children.Clear();
                string actualBadge = Badge ?? "";
                int iconCount = 0;
                Material.Icons.MaterialIconKind iconKind = Material.Icons.MaterialIconKind.Star;

                if (actualBadge == "🔥") 
                {
                   iconCount = 1;
                   iconKind = Material.Icons.MaterialIconKind.Star;
                   actualBadge = "";
                }
                else if (actualBadge == "🚀")
                {
                   iconCount = 1;
                   iconKind = Material.Icons.MaterialIconKind.ArrowUpBold;
                   actualBadge = "";
                }
                else if (actualBadge.StartsWith("STAR:"))
                {
                    var parts = actualBadge.Split('|');
                    if (int.TryParse(parts[0].Substring(5), out int c)) iconCount = c;
                    iconKind = Material.Icons.MaterialIconKind.Star;
                    actualBadge = parts.Length > 1 ? parts[1] : "";
                }
                else if (actualBadge.StartsWith("ARROW:"))
                {
                    var parts = actualBadge.Split('|');
                    if (int.TryParse(parts[0].Substring(6), out int c)) iconCount = c;
                    iconKind = Material.Icons.MaterialIconKind.ArrowUpBold;
                    actualBadge = parts.Length > 1 ? parts[1] : "";
                }

                IBrush fgBrush;
                if (actualBadge.Contains("maintenant") || iconKind == Material.Icons.MaterialIconKind.ArrowUpBold)
                {
                    badge.Background = GetBrush("BadgeGreenBg");
                    fgBrush = GetBrush("BadgeGreenFg");
                }
                else if (actualBadge.Contains("Surveiller"))
                {
                    badge.Background = GetBrush("BadgeOrangeBg");
                    fgBrush = GetBrush("BadgeOrangeFg");
                }
                else
                {
                    badge.Background = GetBrush("BadgeBlueBg");
                    fgBrush = GetBrush("BadgeBlueFg");
                }

                badgeTxt.Foreground = fgBrush;
                badgeTxt.Text = actualBadge;
                badgeTxt.IsVisible = !string.IsNullOrEmpty(actualBadge) || iconCount == 0;

                for (int i = 0; i < iconCount; i++)
                {
                    IBrush iconBrush = fgBrush;
                    if (iconKind == Material.Icons.MaterialIconKind.Star)
                    {
                        iconBrush = GetBrush("BadgeYellow");
                    }

                    var icon = new Material.Icons.Avalonia.MaterialIcon
                    {
                        Kind = iconKind,
                        Width = 12,
                        Height = 12,
                        Foreground = iconBrush
                    };
                    iconsPanel.Children.Add(icon);
                }
                iconsPanel.IsVisible = iconCount > 0;
            }
        }
    }
}