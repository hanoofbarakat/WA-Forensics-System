namespace WpfDesktopClient.Models
{
    public class AuditLogEntry
    {
        public int Id { get; set; }
        public DateTime CreatedAtUtc { get; set; }
        public string ActorUsername { get; set; } = string.Empty;
        public string ActionType { get; set; } = string.Empty;
        public string? TargetUsername { get; set; }
        public string Details { get; set; } = string.Empty;
    }
}
