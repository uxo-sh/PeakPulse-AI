using System;
using System.Linq;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Controls.Shapes;
using Avalonia.Media;

namespace ui_dashboard.Controls;

public partial class LineChart : UserControl
{
    public static readonly StyledProperty<string> TitleProperty      = AvaloniaProperty.Register<LineChart, string>(nameof(Title));
    public static readonly StyledProperty<string> BadgeProperty      = AvaloniaProperty.Register<LineChart, string>(nameof(Badge), "Live");
    public static readonly StyledProperty<string> ColorHexProperty   = AvaloniaProperty.Register<LineChart, string>(nameof(ColorHex), "#00d4ff");
    public static readonly StyledProperty<string> DataPointsProperty = AvaloniaProperty.Register<LineChart, string>(nameof(DataPoints), "60,75,90,85,100,115");

    public string Title      { get => GetValue(TitleProperty);      set => SetValue(TitleProperty, value); }
    public string Badge      { get => GetValue(BadgeProperty);      set => SetValue(BadgeProperty, value); }
    public string ColorHex   { get => GetValue(ColorHexProperty);   set => SetValue(ColorHexProperty, value); }
    public string DataPoints { get => GetValue(DataPointsProperty); set => SetValue(DataPointsProperty, value); }

    private static readonly string[] MonthLabels = { "Oct", "Nov", "Déc", "Jan", "Fév", "Mar" };

    public LineChart() => InitializeComponent();

    protected override void OnLoaded(Avalonia.Interactivity.RoutedEventArgs e)
    {
        base.OnLoaded(e);
        Render();
    }

    protected override void OnSizeChanged(SizeChangedEventArgs e)
    {
        base.OnSizeChanged(e);
        Render();
    }

    private void Render()
    {
        if (this.FindControl<TextBlock>("TitleText") is { } tt) tt.Text = Title;
        if (this.FindControl<TextBlock>("BadgeText")  is { } bt) bt.Text = Badge;

        var canvas = this.FindControl<Canvas>("LineCanvas");
        if (canvas == null) return;
        canvas.Children.Clear();

        double[] vals = DataPoints.Split(',')
            .Select(s => double.TryParse(s.Trim(), out var v) ? v : 0)
            .ToArray();

        if (vals.Length < 2) return;

        double W      = canvas.Bounds.Width > 0 ? canvas.Bounds.Width : 500;
        double H      = 160;
        double maxVal = vals.Max();
        double minVal = vals.Min();
        double range  = maxVal - minVal;
        if (range == 0) range = 1;

        var color = Color.Parse(ColorHex);
        double stepX = W / (vals.Length - 1);

        // Grid lines
        for (int g = 0; g < 4; g++)
        {
            double y = H / 4 * g;
            var line = new Line
            {
                StartPoint = new Point(0, y),
                EndPoint   = new Point(W, y),
                Stroke     = new SolidColorBrush(Color.Parse("#1e2436")),
                StrokeThickness = 1,
            };
            canvas.Children.Add(line);
        }

        // Fill area
        var fillFig = new PathFigure
        {
            StartPoint = new Point(0, H),
            IsClosed   = true
        };
        for (int i = 0; i < vals.Length; i++)
        {
            double x = i * stepX;
            double y = H - (vals[i] - minVal) / range * (H - 20);
            fillFig.Segments!.Add(new LineSegment { Point = new Point(x, y) });
        }
        fillFig.Segments!.Add(new LineSegment { Point = new Point((vals.Length - 1) * stepX, H) });

        var fillGeo = new PathGeometry();
        fillGeo.Figures!.Add(fillFig);
        var fillPath = new Path
        {
            Data = fillGeo,
            Fill = new LinearGradientBrush
            {
                StartPoint = new RelativePoint(0, 0, RelativeUnit.Relative),
                EndPoint   = new RelativePoint(0, 1, RelativeUnit.Relative),
                GradientStops =
                {
                    new GradientStop(Color.FromArgb(60, color.R, color.G, color.B), 0),
                    new GradientStop(Color.FromArgb(0,  color.R, color.G, color.B), 1),
                }
            }
        };
        canvas.Children.Add(fillPath);

        // Line
        var lineFig = new PathFigure { IsClosed = false };
        for (int i = 0; i < vals.Length; i++)
        {
            double x = i * stepX;
            double y = H - (vals[i] - minVal) / range * (H - 20);
            if (i == 0)
                lineFig.StartPoint = new Point(x, y);
            else
                lineFig.Segments!.Add(new LineSegment { Point = new Point(x, y) });
        }
        var lineGeo = new PathGeometry();
        lineGeo.Figures!.Add(lineFig);
        canvas.Children.Add(new Path
        {
            Data            = lineGeo,
            Stroke          = new SolidColorBrush(color),
            StrokeThickness = 2.5,
        });

        // Dots
        for (int i = 0; i < vals.Length; i++)
        {
            double x = i * stepX;
            double y = H - (vals[i] - minVal) / range * (H - 20);
            bool   isLast = i == vals.Length - 1;

            if (isLast)
            {
                // Glow ring
                var glow = new Ellipse
                {
                    Width  = 16, Height = 16,
                    Fill   = new SolidColorBrush(Color.FromArgb(40, color.R, color.G, color.B)),
                };
                Canvas.SetLeft(glow, x - 8);
                Canvas.SetTop(glow,  y - 8);
                canvas.Children.Add(glow);
            }

            var dot = new Ellipse
            {
                Width  = isLast ? 8 : 5,
                Height = isLast ? 8 : 5,
                Fill   = isLast
                    ? new SolidColorBrush(color)
                    : new SolidColorBrush(Color.FromArgb(160, color.R, color.G, color.B)),
            };
            Canvas.SetLeft(dot, x - (isLast ? 4 : 2.5));
            Canvas.SetTop(dot,  y - (isLast ? 4 : 2.5));
            canvas.Children.Add(dot);
        }

        // Labels
        var labelsGrid = this.FindControl<Grid>("LabelsGrid");
        if (labelsGrid == null) return;
        labelsGrid.Children.Clear();
        labelsGrid.ColumnDefinitions.Clear();

        for (int i = 0; i < vals.Length; i++)
        {
            labelsGrid.ColumnDefinitions.Add(new ColumnDefinition(GridLength.Star));
            var lbl = new TextBlock
            {
                Text          = i < MonthLabels.Length ? MonthLabels[i] : "",
                Foreground    = i == vals.Length - 1
                    ? new SolidColorBrush(color)
                    : new SolidColorBrush(Color.Parse("#4a5568")),
                FontSize      = 11,
                TextAlignment = Avalonia.Media.TextAlignment.Center,
                FontWeight    = i == vals.Length - 1 ? FontWeight.Bold : FontWeight.Normal,
            };
            Grid.SetColumn(lbl, i);
            labelsGrid.Children.Add(lbl);
        }
    }
}
