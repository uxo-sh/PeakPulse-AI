using Avalonia.Controls;
using Avalonia.Interactivity;
using Avalonia.Media;

namespace ui_dashboard.Views
{
    public partial class LoginView : UserControl
    {
        public delegate void LoginSuccessHandler(
            string name, string role);
        public event LoginSuccessHandler? OnLoginSuccess;

        public LoginView()
        {
            InitializeComponent();
        }

        private void OnShowLogin(object sender, RoutedEventArgs e)
        {
            SetTab("login");
        }

        private void OnShowSignup(object sender, RoutedEventArgs e)
        {
            SetTab("signup");
        }

        private void SetTab(string tab)
        {
            var loginPanel = this.FindControl<StackPanel>("LoginPanel");
            var signupPanel = this.FindControl<StackPanel>("SignupPanel");
            var loginText = this.FindControl<TextBlock>("LoginTabText");
            var signupText = this.FindControl<TextBlock>("SignupTabText");
            var loginLine = this.FindControl<Border>("LoginTabLine");
            var signupLine = this.FindControl<Border>("SignupTabLine");

            if (tab == "login")
            {
                if (loginPanel != null) loginPanel.IsVisible = true;
                if (signupPanel != null) signupPanel.IsVisible = false;
                if (loginText != null)
                {
                    loginText.Foreground = new SolidColorBrush(
                        Avalonia.Media.Color.Parse("#4fc3f7"));
                    loginText.FontWeight = FontWeight.Bold;
                }
                if (signupText != null)
                {
                    signupText.Foreground = new SolidColorBrush(
                        Avalonia.Media.Color.Parse("#3a4a5c"));
                    signupText.FontWeight = FontWeight.Normal;
                }
                if (loginLine != null)
                    loginLine.Background = new SolidColorBrush(
                        Avalonia.Media.Color.Parse("#4fc3f7"));
                if (signupLine != null)
                    signupLine.Background = new SolidColorBrush(
                        Avalonia.Media.Colors.Transparent);
            }
            else
            {
                if (loginPanel != null) loginPanel.IsVisible = false;
                if (signupPanel != null) signupPanel.IsVisible = true;
                if (signupText != null)
                {
                    signupText.Foreground = new SolidColorBrush(
                        Avalonia.Media.Color.Parse("#4fc3f7"));
                    signupText.FontWeight = FontWeight.Bold;
                }
                if (loginText != null)
                {
                    loginText.Foreground = new SolidColorBrush(
                        Avalonia.Media.Color.Parse("#3a4a5c"));
                    loginText.FontWeight = FontWeight.Normal;
                }
                if (signupLine != null)
                    signupLine.Background = new SolidColorBrush(
                        Avalonia.Media.Color.Parse("#4fc3f7"));
                if (loginLine != null)
                    loginLine.Background = new SolidColorBrush(
                        Avalonia.Media.Colors.Transparent);
            }
        }

        private void OnLoginClick(object sender, RoutedEventArgs e)
        {
            var email = this.FindControl<TextBox>("LoginEmail")?.Text ?? "";
            OnLoginSuccess?.Invoke(email, "Analyste");
        }

        private void OnSignupClick(object sender, RoutedEventArgs e)
        {
            var name = this.FindControl<TextBox>("SignupName")?.Text ?? "Utilisateur";
            OnLoginSuccess?.Invoke(name, "Analyste");
        }
    }
}