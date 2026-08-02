namespace WpfDesktopClient.Models
{
    public class CaseInfo
    {
        public string CaseId { get; set; }
        public string Title { get; set; }
        public string LeadInvestigator { get; set; }
        public string Status { get; set; }
        public DateTime CreatedAt { get; set; }
        public DateTime LastUpdatedAt { get; set; }
        public string CaseGuid { get; set; }
    }
}
