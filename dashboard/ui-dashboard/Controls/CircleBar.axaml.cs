using System;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Controls.Shapes;
using Avalonia.Media;

namespace ui_dashboard.Controls
{
    public partial class CircleBar : UserControl
    {
        public static readonly StyledProperty<string> TitleProperty =
            AvaloniaProperty.Register<CircleBar, string>(nameof(Title));
        public static readonly StyledProperty<double> ValueProperty =
            AvaloniaProperty.Register<CircleBar, double>(nameof(Value));
        public static readonly StyledProperty<double> MaxValueProperty =
            AvaloniaProperty.Register<CircleBar, double>(nameof(MaxValue), 100);
        public static readonly StyledProperty<string> LabelProperty =
            AvaloniaProperty.Register<CircleBar, string>(nameof(Label));
        public static readonly StyledProperty<string> ColorHexProperty =
            AvaloniaProperty.Register<CircleBar, string>(nameof(ColorHex), "#4fc3f7");
        public static readonly StyledProperty<string> ValueSuffixProperty =
            AvaloniaProperty.Register<CircleBar, string>(nameof(ValueSuffix), "%");

        public string Title
        {
            get => GetValue(TitleProperty);
            set => SetValue(TitleProperty, value);
        }
        public double Value
        {
            get => GetValue(ValueProperty);
            set => SetValue(ValueProperty, value);
        }
        public double MaxValue
        {
            get => GetValue(MaxValueProperty);
            set => SetValue(MaxValueProperty, value);
        }
        public string Label
        {
            get => GetValue(LabelProperty);
            set => SetValue(LabelProperty, value);
        }
        public string ColorHex
        {
            get => GetValue(ColorHexProperty);
            set => SetValue(ColorHexProperty, value);
        }
        public string ValueSuffix
        {
            get => GetValue(ValueSuffixProperty);
            set => SetValue(ValueSuffixProperty, value);
        }

        public CircleBar()
        {
            InitializeComponent();
        }

        protected override void OnLoaded(
            Avalonia.Interactivity.RoutedEventArgs e)
        {
            base.OnLoaded(e);
            DrawCircle();
        }

        private void DrawCircle()
        {
            var canvas = this.FindControl<Canvas>("CircleCanvas");
            if (canvas == null) return;
            canvas.Children.Clear();

            double cx = 60, cy = 60, r = 45;
            double strokeWidth = 10;
            double percent = Math.Clamp(Value / MaxValue, 0, 1);
            double angle = percent * 360;

            // Cercle de fond
            var bgCircle = new Ellipse
            {
                Width = r * 2,
                Height = r * 2,
                Stroke = new SolidColorBrush(
                    Color.Parse("#1e2d40")),
                StrokeThickness = strokeWidth,
                Fill = Brushes.Transparent
            };
            Canvas.SetLeft(bgCircle, cx - r);
            Canvas.SetTop(bgCircle, cy - r);
            canvas.Children.Add(bgCircle);

            // Arc de progression
            if (angle > 0)
            {
                var arcPath = CreateArc(cx, cy, r, 0, angle,
                    strokeWidth);
                arcPath.Stroke = new SolidColorBrush(
                    Color.Parse(ColorHex));
                arcPath.StrokeThickness = strokeWidth;
                arcPath.StrokeLineCap = PenLineCap.Round;
                arcPath.Fill = Brushes.Transparent;
                canvas.Children.Add(arcPath);
            }

            // Texte valeur
            if (this.FindControl<TextBlock>("ValueText")
                    is TextBlock val)
            {
                val.Text = $"{Value}{ValueSuffix}";
                val.Foreground = new SolidColorBrush(
                    Color.Parse(ColorHex));
            }

            if (this.FindControl<TextBlock>("TitleText")
                    is TextBlock title)
                title.Text = Title;

            if (this.FindControl<TextBlock>("LabelText")
                    is TextBlock lbl)
                lbl.Text = Label;
        }

        private Path CreateArc(double cx, double cy, double r,
            double startAngle, double sweepAngle, double strokeW)
        {
            startAngle -= 90;
            double endAngle = startAngle + sweepAngle;

            double startRad = startAngle * Math.PI / 180;
            double endRad = endAngle * Math.PI / 180;

            double x1 = cx + r * Math.Cos(startRad);
            double y1 = cy + r * Math.Sin(startRad);
            double x2 = cx + r * Math.Cos(endRad);
            double y2 = cy + r * Math.Sin(endRad);

            bool largeArc = sweepAngle > 180;

            var geo = new StreamGeometry();
            using (var ctx = geo.Open())
            {
                ctx.BeginFigure(new Point(x1, y1), false);
                ctx.ArcTo(new Point(x2, y2),
                    new Size(r, r), 0, largeArc,
                    SweepDirection.Clockwise);
            }

            return new Path { Data = geo };
        }
    }
}