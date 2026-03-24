using System;
using System.Threading.Tasks;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Interactivity;
using Avalonia.Media;
using ui_dashboard.Views;
using ui_dashboard.Services;
using Material.Icons;
using Material.Icons.Avalonia;

namespace ui_dashboard
{
    public partial class MainWindow : Window
    {
        private string _userName = "Utilisateur";
        private string _userRole = "Analyste";
        private bool _isDarkMode = true;

        public MainWindow()
        {
            InitializeComponent();
            ShowLogin();
        }

        private void OnThemeClick(object sender, RoutedEventArgs e)
        {
            _isDarkMode = !_isDarkMode;
            var themeIcon = this.FindControl<MaterialIcon>("ThemeIcon");

            if (_isDarkMode)
            {
                Application.Current!.RequestedThemeVariant =
                    Avalonia.Styling.ThemeVariant.Dark;
                if (themeIcon != null)
                    themeIcon.Kind = MaterialIconKind.MonitorShimmer;
            }
            else
            {
                Application.Current!.RequestedThemeVariant =
                    Avalonia.Styling.ThemeVariant.Light;
                if (themeIcon != null)
                    themeIcon.Kind = MaterialIconKind.Monitor;
            }
        }

        private void ShowLogin()
        {
            var content = this.FindControl<ContentControl>("MainContent");
            var sidebar = this.FindControl<Border>("SidebarBorder");

            if (sidebar != null) sidebar.IsVisible = false;

            if (content != null)
            {
                Grid.SetColumn(content, 0);
                Grid.SetColumnSpan(content, 2);
            }

            var loginView = new LoginView();
            loginView.OnLoginSuccess += OnLoginSuccess;
            if (content != null) content.Content = loginView;
        }

        private void OnLoginSuccess(string name, string role)
        {
            _userName = name;
            _userRole = role;

            var content = this.FindControl<ContentControl>("MainContent");
            var sidebar = this.FindControl<Border>("SidebarBorder");

            if (content != null)
            {
                Grid.SetColumn(content, 1);
                Grid.SetColumnSpan(content, 1);
            }

            if (sidebar != null) sidebar.IsVisible = true;

            if (this.FindControl<TextBlock>("UserNameText")
                    is TextBlock nameText)
                nameText.Text = _userName;

            if (this.FindControl<TextBlock>("UserRoleText")
                    is TextBlock roleText)
                roleText.Text = _userRole;

            NavigateTo("games");

            // Vérifie le statut de l'API
            _ = CheckApiStatusAsync();
        }

        private async Task CheckApiStatusAsync()
        {
            var isOnline = await ApiService.Instance.CheckHealthAsync();

            Avalonia.Threading.Dispatcher.UIThread.Post(() =>
            {
                var icon = this.FindControl<MaterialIcon>("ApiStatusIcon");
                if (icon != null)
                    icon.Foreground = isOnline
                        ? new SolidColorBrush(
                            Avalonia.Media.Color.Parse("#4caf50"))
                        : new SolidColorBrush(
                            Avalonia.Media.Color.Parse("#ff6b6b"));
            });
        }

        private void NavigateTo(string domain)
        {
            var content = this.FindControl<ContentControl>("MainContent");
            if (content == null) return;

            content.Content = new DomainView(domain);
            ResetButtons();
            SetActive("Btn" + char.ToUpper(domain[0]) +
                      domain.Substring(1));
        }

        private void ResetButtons()
        {
            string[] btns = { "BtnGames", "BtnMovies", "BtnPipeline", "BtnDatabase" };
            foreach (var name in btns)
            {
                if (this.FindControl<Button>(name) is Button btn)
                {
                    btn.Background = new SolidColorBrush(
                        Avalonia.Media.Colors.Transparent);

                    var icon = btn.Content as StackPanel;
                    if (icon?.Children[0] is MaterialIcon mi)
                        mi.Foreground = new SolidColorBrush(
                            Avalonia.Media.Color.Parse("#5a7a9c"));
                    if (icon?.Children[1] is TextBlock tb)
                        tb.Foreground = new SolidColorBrush(
                            Avalonia.Media.Color.Parse("#5a7a9c"));
                }
            }
        }

        private void SetActive(string name)
        {
            if (this.FindControl<Button>(name) is Button btn)
            {
                btn.Background = new SolidColorBrush(
                    Avalonia.Media.Color.Parse("#1a2744"));

                var icon = btn.Content as StackPanel;
                if (icon?.Children[0] is MaterialIcon mi)
                    mi.Foreground = new SolidColorBrush(
                        Avalonia.Media.Color.Parse("#4fc3f7"));
                if (icon?.Children[1] is TextBlock tb)
                    tb.Foreground = new SolidColorBrush(
                        Avalonia.Media.Color.Parse("#4fc3f7"));
            }
        }

        private void OnRefreshClick(object sender, RoutedEventArgs e)
        {
            var content = this.FindControl<ContentControl>("MainContent");
            if (content?.Content is DomainView current)
                content.Content = new DomainView(current.Domain);
        }

        private void OnPipelineClick(object sender, RoutedEventArgs e)
        {
            var content = this.FindControl<ContentControl>("MainContent");
            if (content == null) return;
            content.Content = new Views.PipelineView();
            ResetButtons();
            SetActive("BtnPipeline");
        }

        private void OnDatabaseClick(object sender, RoutedEventArgs e)
        {
            var content = this.FindControl<ContentControl>("MainContent");
            if (content == null) return;
            content.Content = new Views.DatabaseView();
            ResetButtons();
            SetActive("BtnDatabase");
        }

        private void OnGamesClick(object sender, RoutedEventArgs e)
            => NavigateTo("games");
        private void OnMoviesClick(object sender, RoutedEventArgs e)
            => NavigateTo("movies");
        private void OnLogoutClick(object sender, RoutedEventArgs e)
            => ShowLogin();
    }
}