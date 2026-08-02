namespace WpfDesktopClient.Models
{
    public enum UserStatus { Active, Disabled }

    public class ManagedUser
    {
        public int Id { get; set; }
        public string Username { get; set; } = string.Empty;
        public string PasswordHash { get; set; } = string.Empty;
        public UserRole Role { get; set; }
        public UserStatus Status { get; set; }
        public DateTime CreatedAtUtc { get; set; }
        public DateTime? LastLoginUtc { get; set; }
        public DateTime? PasswordChangedAtUtc { get; set; }
    }
}
