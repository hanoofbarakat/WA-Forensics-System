using System;

namespace WpfDesktopClient.Models
{
    public class TimelineFilterState
    {
        public string? SearchText { get; set; }
        public long? SelectedChatId { get; set; }
        public string? SelectedEventType { get; set; }

        public DateTime? DateFromUtc { get; set; }
        public DateTime? DateToUtc { get; set; }

        public bool ShowDeletedOnly { get; set; }
        public bool ShowRecoveredOnly { get; set; }
        public bool ShowSuspiciousOnly { get; set; }
        public bool HasMediaOnly { get; set; }
    }
}