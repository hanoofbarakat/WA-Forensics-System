using System;

namespace WpfDesktopClient.Models
{
    public class CaseActivityEntry
    {
        public int Id { get; set; }
        public string CaseGuid { get; set; }
        public string ActorUsername { get; set; }
        public string ActionType { get; set; }
        public string Details { get; set; }
        public DateTime CreatedAtUtc { get; set; }
    }
}
