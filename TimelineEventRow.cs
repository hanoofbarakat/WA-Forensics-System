using System;

namespace WpfDesktopClient.Models
{
    public class TimelineEventRow
    {
        public long EventId { get; set; }
        public long TsUnix { get; set; }
        public string? TsIso { get; set; }
        public string? EventType { get; set; }

        public long? ChatId { get; set; }
        public long? MessageId { get; set; }

        public string? Sender { get; set; }
        public string? Snippet { get; set; }
        public bool IsDeleted { get; set; }
        public string? Source { get; set; }

        public string? ChatName { get; set; }
        public string? Phone { get; set; }
        public string? Jid { get; set; }

        public string? MessageText { get; set; }
        public long? MessageTimestamp { get; set; }
        public bool IsRecovered { get; set; }
        public bool IsDeletedRecovered { get; set; }
        public string? RecoverySource { get; set; }
        public string? RecoveryMethod { get; set; }
        public string? RecoveredAt { get; set; }

        public string? MediaPath { get; set; }
        public string? MimeType { get; set; }

        public string? SuspiciousPatternType { get; set; }
        public int? SuspiciousSeverity { get; set; }
        public string? SuspiciousDescription { get; set; }
    }
}