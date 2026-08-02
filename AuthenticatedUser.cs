using WpfDesktopClient.Models;

namespace WpfDesktopClient.Models
{
    public class AuthenticatedUser
    {
        public string Username { get; set; }
        public UserRole Role { get; set; }
    }
}
