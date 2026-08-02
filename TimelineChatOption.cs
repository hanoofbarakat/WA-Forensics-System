namespace WpfDesktopClient.Models
{
    public class TimelineChatOption
    {
        public long ChatId { get; set; }
        public string? Name { get; set; }
        public string? Phone { get; set; }
        public string? Jid { get; set; }

        public string DisplayName =>
            !string.IsNullOrWhiteSpace(Name) ? Name! :
            !string.IsNullOrWhiteSpace(Phone) ? Phone! :
            !string.IsNullOrWhiteSpace(Jid) ? Jid! :
            "Unknown Chat";
    }
}