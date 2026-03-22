using Avalonia;
using Avalonia.Controls;
using Avalonia.Media;

namespace ui_dashboard.Controls
{
    public partial class BarChart : UserControl
    {
        public static readonly StyledProperty<string> TitleProperty =
            AvaloniaProperty.Register<BarChart, string>(
                nameof(Title), "Évolution — 6 derniers mois");

        public static readonly StyledProperty<string> BadgeProperty =
            AvaloniaProperty.Register<BarChart, string>(
                nameof(Badge), "Live");

        public static readonly StyledProperty<string> BarColorProperty =
            AvaloniaProperty.Register<BarChart, string>(
                nameof(BarColor), "#4fc3f7");

        // Hauteurs des 6 barres séparées par virgule
        public static readonly StyledProperty<string> HeightsProperty =
            AvaloniaProperty.Register<BarChart, string>(
                nameof(Heights), "60,75,90,85,100,115");

        public string Title
        {
            get => GetValue(TitleProperty);
            set => SetValue(TitleProperty, value);
        }
        public string Badge
        {
            get => GetValue(BadgeProperty);
            set => SetValue(BadgeProperty, value);
        }
        public string BarColor
        {
            get => GetValue(BarColorProperty);
            set => SetValue(BarColorProperty, value);
        }
        public string Heights
        {
            get => GetValue(HeightsProperty);
            set => SetValue(HeightsProperty, value);
        }

        public BarChart()
        {
            InitializeComponent();
        }

        protected override void OnLoaded(
            Avalonia.Interactivity.RoutedEventArgs e)
        {
            base.OnLoaded(e);
            UpdateUI();
        }

        private void UpdateUI()
        {
            if (this.FindControl<TextBlock>("ChartTitle")
                    is TextBlock title)
                title.Text = Title;

            if (this.FindControl<TextBlock>("ChartBadge")
                    is TextBlock badge)
                badge.Text = Badge;

            if (this.FindControl<Grid>("BarsGrid") is Grid grid)
            {
                var heights = Heights.Split(',');
                // var maxH = 115.0;
                var colors = new[]
                {
                    "#1a2744","#1e3a6e","#1e4a8e",
                    "#2255aa","#2a6acc", BarColor
                };

                grid.Children.Clear();

                for (int i = 0; i < 6; i++)
                {
                    double h = i < heights.Length
                        ? double.Parse(heights[i]) : 60;

                    var bar = new Border
                    {
                        Height = h,
                        Background = new SolidColorBrush(
                            Color.Parse(colors[i])),
                        CornerRadius = new CornerRadius(4, 4, 0, 0)
                    };

                    var sp = new StackPanel
                    {
                        VerticalAlignment =
                            Avalonia.Layout.VerticalAlignment.Bottom,
                        Margin = new Thickness(4, 0)
                    };
                    sp.Children.Add(bar);

                    Grid.SetColumn(sp, i);
                    grid.Children.Add(sp);
                }
            }
        }
    }
}