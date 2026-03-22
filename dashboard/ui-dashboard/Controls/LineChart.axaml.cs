using System;
using System.Globalization;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Controls.Shapes;
using Avalonia.Input;
using Avalonia.Media;

namespace ui_dashboard.Controls
{
    public partial class LineChart : UserControl
    {
        public static readonly StyledProperty<string> TitleProperty =
            AvaloniaProperty.Register<LineChart, string>(
                nameof(Title), "Évolution");
        public static readonly StyledProperty<string> BadgeProperty =
            AvaloniaProperty.Register<LineChart, string>(
                nameof(Badge), "Live");
        public static readonly StyledProperty<string> ColorHexProperty =
            AvaloniaProperty.Register<LineChart, string>(
                nameof(ColorHex), "#4fc3f7");
        public static readonly StyledProperty<string> DataPointsProperty =
            AvaloniaProperty.Register<LineChart, string>(
                nameof(DataPoints), "60,75,90,85,100,115");

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
        public string ColorHex
        {
            get => GetValue(ColorHexProperty);
            set => SetValue(ColorHexProperty, value);
        }
        public string DataPoints
        {
            get => GetValue(DataPointsProperty);
            set => SetValue(DataPointsProperty, value);
        }

        private double[] _values = [];
        private Point[] _pts = [];
        private double _chartW = 800;
        private double _chartH = 160;

        public LineChart()
        {
            InitializeComponent();
        }

        protected override void OnLoaded(
            Avalonia.Interactivity.RoutedEventArgs e)
        {
            base.OnLoaded(e);

            var canvas = this.FindControl<Canvas>("ChartCanvas");
            if (canvas != null)
            {
                canvas.PointerMoved += OnPointerMoved;
                canvas.PointerExited += OnPointerExited;
                canvas.SizeChanged += (s, ev) => BuildChart();
            }

            BuildChart();
        }

        protected override void OnPropertyChanged(
            AvaloniaPropertyChangedEventArgs change)
        {
            base.OnPropertyChanged(change);
            if (change.Property == DataPointsProperty ||
                change.Property == ColorHexProperty   ||
                change.Property == TitleProperty      ||
                change.Property == BadgeProperty)
                BuildChart();
        }

        private void BuildChart()
        {
            if (this.FindControl<TextBlock>("ChartTitle")
                    is TextBlock title)
                title.Text = Title;
            if (this.FindControl<TextBlock>("ChartBadge")
                    is TextBlock badge)
                badge.Text = Badge;

            var canvas = this.FindControl<Canvas>("ChartCanvas");
            var yCanvas = this.FindControl<Canvas>("YAxisCanvas");
            var xGrid = this.FindControl<Grid>("XAxisGrid");
            if (canvas == null) return;

            canvas.Children.Clear();
            if (yCanvas != null) yCanvas.Children.Clear();

            var rawPoints = DataPoints.Split(',');
            _values = new double[rawPoints.Length];
            for (int i = 0; i < rawPoints.Length; i++)
                double.TryParse(rawPoints[i],
                    NumberStyles.Any,
                    CultureInfo.InvariantCulture,
                    out _values[i]);

            double max = 130;
            double min = 40;
            int count = _values.Length;
            _chartH = 160;

            _chartW = canvas.Bounds.Width > 10
                ? canvas.Bounds.Width
                : 800;

            _pts = new Point[count];
            for (int i = 0; i < count; i++)
            {
                double x = i * (_chartW / (count - 1));
                double y = _chartH -
                    ((_values[i] - min) / (max - min) * _chartH);
                _pts[i] = new Point(x, y);
            }

            var color = Color.Parse(ColorHex);

            // ── 1. Lignes de grille ──────────────────────────
            int gridLines = 5;
            for (int g = 0; g <= gridLines; g++)
            {
                double y = g * (_chartH / gridLines);
                canvas.Children.Add(new Line
                {
                    StartPoint = new Point(0, y),
                    EndPoint = new Point(_chartW, y),
                    Stroke = new SolidColorBrush(
                        Color.Parse("#1e2d40")),
                    StrokeThickness = 0.5,
                    StrokeDashArray =
                        new Avalonia.Collections
                            .AvaloniaList<double> { 5, 5 }
                });

                if (yCanvas != null)
                {
                    double val = max -
                        g * ((max - min) / gridLines);
                    var lbl = new TextBlock
                    {
                        Text = ((int)val).ToString(),
                        FontSize = 10,
                        Foreground = new SolidColorBrush(
                            Color.Parse("#3a4a5c")),
                    };
                    Canvas.SetLeft(lbl, 0);
                    Canvas.SetTop(lbl, y - 8);
                    yCanvas.Children.Add(lbl);
                }
            }

            // ── 2. Zone remplie (au dessus de la grille) ────
            var fillGeo = new StreamGeometry();
            using (var ctx = fillGeo.Open())
            {
                ctx.BeginFigure(
                    new Point(_pts[0].X, _chartH), false);
                ctx.LineTo(_pts[0]);
                for (int i = 1; i < _pts.Length; i++)
                    ctx.LineTo(_pts[i]);
                ctx.LineTo(
                    new Point(_pts[^1].X, _chartH));
                ctx.EndFigure(true);
            }
            canvas.Children.Add(new Path
            {
                Data = fillGeo,
                // ✅ Opacité augmentée pour mieux voir la couleur
                Fill = new SolidColorBrush(Color.FromArgb(
                    80, color.R, color.G, color.B)),
                Stroke = Brushes.Transparent,
                StrokeThickness = 0
            });

            // ── 3. Ligne principale ──────────────────────────
            for (int i = 0; i < _pts.Length - 1; i++)
            {
                canvas.Children.Add(new Line
                {
                    StartPoint = _pts[i],
                    EndPoint = _pts[i + 1],
                    Stroke = new SolidColorBrush(color),
                    StrokeThickness = 2.5,
                    StrokeLineCap = PenLineCap.Round
                });
            }

            // ── 4. Points sur la courbe ──────────────────────
            foreach (var pt in _pts)
            {
                var outer = new Ellipse
                {
                    Width = 10, Height = 10,
                    Fill = new SolidColorBrush(color),
                    Stroke = new SolidColorBrush(
                        Color.FromArgb(80,
                            color.R, color.G, color.B)),
                    StrokeThickness = 3
                };
                Canvas.SetLeft(outer, pt.X - 5);
                Canvas.SetTop(outer, pt.Y - 5);
                canvas.Children.Add(outer);

                var inner = new Ellipse
                {
                    Width = 5, Height = 5,
                    Fill = Brushes.White
                };
                Canvas.SetLeft(inner, pt.X - 2.5);
                Canvas.SetTop(inner, pt.Y - 2.5);
                canvas.Children.Add(inner);
            }

            // ── 5. Labels axe X ─────────────────────────────
            if (xGrid != null)
            {
                xGrid.ColumnDefinitions.Clear();
                xGrid.Children.Clear();
                string[] months =
                    { "Oct","Nov","Déc","Jan","Fév","Mar" };
                for (int i = 0; i < months.Length; i++)
                {
                    xGrid.ColumnDefinitions.Add(
                        new ColumnDefinition(GridLength.Star));
                    var lbl = new TextBlock
                    {
                        Text = months[i],
                        FontSize = 10,
                        Foreground = i == months.Length - 1
                            ? new SolidColorBrush(
                                Color.Parse(ColorHex))
                            : new SolidColorBrush(
                                Color.Parse("#3a4a5c")),
                        FontWeight = i == months.Length - 1
                            ? FontWeight.Bold
                            : FontWeight.Normal,
                        HorizontalAlignment =
                            Avalonia.Layout.HorizontalAlignment
                                .Center
                    };
                    Grid.SetColumn(lbl, i);
                    xGrid.Children.Add(lbl);
                }
            }
        }

        private void OnPointerMoved(object? sender,
            PointerEventArgs e)
        {
            if (_pts.Length == 0) return;
            var canvas = this.FindControl<Canvas>("ChartCanvas");
            var tooltip = this.FindControl<Border>("TooltipBorder");
            var tooltipText =
                this.FindControl<TextBlock>("TooltipText");
            if (canvas == null || tooltip == null) return;

            var pos = e.GetPosition(canvas);
            int closest = 0;
            double minDist = double.MaxValue;
            for (int i = 0; i < _pts.Length; i++)
            {
                double dist = Math.Abs(_pts[i].X - pos.X);
                if (dist < minDist)
                {
                    minDist = dist;
                    closest = i;
                }
            }

            if (minDist < 60)
            {
                if (tooltipText != null)
                    tooltipText.Text =
                        $"Score : {(int)_values[closest]}";
                tooltip.IsVisible = true;
                Canvas.SetLeft(tooltip,
                    _pts[closest].X + 10);
                Canvas.SetTop(tooltip,
                    _pts[closest].Y - 30);
            }
            else
            {
                tooltip.IsVisible = false;
            }
        }

        private void OnPointerExited(object? sender,
            PointerEventArgs e)
        {
            var tooltip =
                this.FindControl<Border>("TooltipBorder");
            if (tooltip != null) tooltip.IsVisible = false;
        }
    }
}