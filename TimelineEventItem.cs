using System;

namespace WpfDesktopClient.Models
{
    public class TimelineEventItem
    {
        public long EventId { get; set; }
        public DateTime EventTimeUtc { get; set; }
        public string EventType { get; set; } = string.Empty;

        public long? ChatId { get; set; }
        public long? MessageId { get; set; }

        public string Sender { get; set; } = string.Empty;
        public string Snippet { get; set; } = string.Empty;
        public bool IsDeleted { get; set; }
        public bool IsRecovered { get; set; }
        public bool IsDeletedRecovered { get; set; }
        public bool IsDeletedAndRecovered { get; set; }
        
        public bool IsMarkedAsDeletedAndRecovered => IsDeleted && IsRecovered;

        public string? RecoverySource { get; set; }
        public string? RecoveryMethod { get; set; }
        public string? RecoveredAt { get; set; }

        public string? Source { get; set; }

        public string? ChatName { get; set; }
        public string? Phone { get; set; }
        public string? Jid { get; set; }

        public string? MediaPath { get; set; }
        public string? MimeType { get; set; }

        public bool IsSuspicious { get; set; }
        public string? SuspiciousPatternType { get; set; }
        public int? SuspiciousSeverity { get; set; }
        public string? SuspiciousDescription { get; set; }

        public bool ShowDateHeader { get; set; }
        public string? DateHeaderText { get; set; }

        public string DisplayDate => EventTimeUtc.ToLocalTime().ToString("yyyy-MM-dd");
        public string DisplayTime => EventTimeUtc.ToLocalTime().ToString("HH:mm:ss");

        public string ChatDisplayName =>
            !string.IsNullOrWhiteSpace(ChatName) ? ChatName! :
            !string.IsNullOrWhiteSpace(Phone) ? Phone! :
            !string.IsNullOrWhiteSpace(Jid) ? Jid! :
            "Unknown Chat";

        public string DisplayTitle
        {
            get
            {
                if (IsDeletedRecovered) return "Recovered Deleted Message";
                if (IsRecovered) return "Recovered Message";
                if (IsDeleted) return "Deleted Message";
                if (!string.IsNullOrWhiteSpace(MimeType) || !string.IsNullOrWhiteSpace(MediaPath)) return "Media Event";
                if (!string.IsNullOrWhiteSpace(EventType)) return EventType;
                return "Timeline Event";
            }
        }

        public string DisplaySubtitle =>
            !string.IsNullOrWhiteSpace(Snippet) ? Snippet :
            !string.IsNullOrWhiteSpace(Source) ? Source! :
            "No additional details";

        public bool HasMedia => !string.IsNullOrWhiteSpace(MediaPath) || !string.IsNullOrWhiteSpace(MimeType);
        public bool HasRecoveryInfo => IsRecovered || IsDeletedRecovered;
        public bool HasSuspiciousInfo => IsSuspicious || !string.IsNullOrWhiteSpace(SuspiciousPatternType);
    }
}