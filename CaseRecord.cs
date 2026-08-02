using System;

namespace WpfDesktopClient.Models
{
    public class CaseRecord
    {
        public int Id { get; set; }
        public string CaseGuid { get; set; }
        public string CaseNumber { get; set; }
        public string Title { get; set; }
        public string ReferenceNumber { get; set; }
        public string RequestingAuthority { get; set; }
        public string LeadInvestigatorUsername { get; set; }
        public string SourceDevice { get; set; }
        public string DeviceIdentifier { get; set; }
        public string AcquisitionMethod { get; set; }
        public string AcquisitionTool { get; set; }
        public string ReportDbPath { get; set; }
        public DateTime? AcquisitionTimeUtc { get; set; }
        public CaseStatus Status { get; set; }
        public CasePriority Priority { get; set; }
        public string CreatedBy { get; set; }
        public DateTime CreatedAtUtc { get; set; }
        public DateTime UpdatedAtUtc { get; set; }
        public DateTime? ClosedAtUtc { get; set; }

        // =========================
        // 🔥 خصائص العرض (IMPORTANT)
        // =========================

        // يستخدم في DataGrid بدل CaseNumber
        public string CaseId => CaseNumber;

        // عرض اسم المحقق بشكل نظيف
        public string LeadInvestigator =>
            string.IsNullOrWhiteSpace(LeadInvestigatorUsername)
                ? "[Unassigned]"
                : LeadInvestigatorUsername;

        // تحويل التوقيت إلى Local Time
        public DateTime CreatedAt => CreatedAtUtc.ToLocalTime();

        public DateTime LastUpdatedAt => UpdatedAtUtc.ToLocalTime();

        // عرض القيم الفارغة بشكل احترافي
        public string DisplayReference =>
            string.IsNullOrWhiteSpace(ReferenceNumber)
                ? "[Not Specified]"
                : ReferenceNumber;

        public string DisplaySourceDevice =>
            string.IsNullOrWhiteSpace(SourceDevice)
                ? "[Not Specified]"
                : SourceDevice;

        public string DisplayAcquisitionMethod =>
            string.IsNullOrWhiteSpace(AcquisitionMethod)
                ? "[Not Specified]"
                : AcquisitionMethod;

        public string DisplayAcquisitionTool =>
            string.IsNullOrWhiteSpace(AcquisitionTool)
                ? "[Not Specified]"
                : AcquisitionTool;

        public string DisplayCreatedBy =>
            string.IsNullOrWhiteSpace(CreatedBy)
                ? "[Unknown]"
                : CreatedBy;

        public string ClosedAtDisplay =>
            ClosedAtUtc == null
                ? "-"
                : ClosedAtUtc.Value.ToLocalTime().ToString("yyyy-MM-dd HH:mm");
    }
}