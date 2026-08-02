using System;

namespace WpfDesktopClient.Models
{
    public class TimelineSummaryRow
    {
        public int TotalEvents { get; set; }
        public int DeletedEvents { get; set; }
        public int RecoveredEvents { get; set; }
        public int DeletedRecoveredEvents { get; set; }
        public int SuspiciousPatterns { get; set; }
        public int ChatsCount { get; set; }
        public int RiskScore { get; set; }
        public string? RiskLevel { get; set; }

        public DateTime? FirstEventAtUtc { get; set; }
        public DateTime? LastEventAtUtc { get; set; }
    }
}