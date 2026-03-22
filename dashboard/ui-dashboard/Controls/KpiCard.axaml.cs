using System;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Media;
using Material.Icons;
using Material.Icons.Avalonia;

namespace ui_dashboard.Controls
{
    public partial class KpiCard : UserControl
    {
        public static readonly StyledProperty<string> LabelProperty =
            AvaloniaProperty.Register<KpiCard, string>(nameof(Label));
        public static readonly StyledProperty<string> ValueProperty =
            AvaloniaProperty.Register<KpiCard, string>(nameof(Value));
        public static readonly StyledProperty<string> TrendProperty =
            AvaloniaProperty.Register<KpiCard, string>(nameof(Trend));
        public static readonly StyledProperty<string> SubLabelProperty =
            AvaloniaProperty.Register<KpiCard, string>(nameof(SubLabel));
        public static readonly StyledProperty<string> ColorHexProperty =
            AvaloniaProperty.Register<KpiCard, string>(
                nameof(ColorHex), "#4fc3f7");
        public static readonly StyledProperty<string> IconKindProperty =
            AvaloniaProperty.Register<KpiCard, string>(
                nameof(IconKind), "ChartBar");

        public string Label
        {
            get => GetValue(LabelProperty);
            set => SetValue(LabelProperty, value);
        }
        public string Value
        {
            get => GetValue(ValueProperty);
            set => SetValue(ValueProperty, value);
        }
        public string Trend
        {
            get => GetValue(TrendProperty);
            set => SetValue(TrendProperty, value);
        }
        public string SubLabel
        {
            get => GetValue(SubLabelProperty);
            set => SetValue(SubLabelProperty, value);
        }
        public string ColorHex
        {
            get => GetValue(ColorHexProperty);
            set => SetValue(ColorHexProperty, value);
        }
        public string IconKind
        {
            get => GetValue(IconKindProperty);
            set => SetValue(IconKindProperty, value);
        }

        public KpiCard()
        {
            InitializeComponent();
        }

        protected override void OnLoaded(
            Avalonia.Interactivity.RoutedEventArgs e)
        {
            base.OnLoaded(e);
            UpdateUI();
        }

        // ✅ Se met à jour automatiquement quand une propriété change
        protected override void OnPropertyChanged(
            AvaloniaPropertyChangedEventArgs change)
        {
            base.OnPropertyChanged(change);
            if (change.Property == ValueProperty   ||
                change.Property == LabelProperty   ||
                change.Property == TrendProperty   ||
                change.Property == SubLabelProperty ||
                change.Property == ColorHexProperty ||
                change.Property == IconKindProperty)
            {
                UpdateUI();
            }
        }

        private void UpdateUI()
        {
            var colorHex = string.IsNullOrEmpty(ColorHex)
                ? "#4fc3f7" : ColorHex;
            var color = Color.Parse(colorHex);
            var brush = new SolidColorBrush(color);

            if (this.FindControl<TextBlock>("LabelText")
                    is TextBlock lbl)
                lbl.Text = Label ?? "";

            if (this.FindControl<TextBlock>("ValueText")
                    is TextBlock val)
            {
                val.Text = Value ?? "";
                val.Foreground = brush;
            }

            if (this.FindControl<TextBlock>("TrendText")
                    is TextBlock trend)
            {
                trend.Text = (Trend ?? "") + " ";
                trend.Foreground = new SolidColorBrush(
                    Color.Parse("#4caf50"));
            }

            if (this.FindControl<TextBlock>("SubText")
                    is TextBlock sub)
                sub.Text = SubLabel ?? "";

            if (this.FindControl<MaterialIcon>("CardIcon")
                    is MaterialIcon icon)
            {
                if (Enum.TryParse<MaterialIconKind>(
                        IconKind, out var kind))
                    icon.Kind = kind;
                icon.Foreground = brush;
            }
        }
    }
}