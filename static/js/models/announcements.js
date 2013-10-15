$(document).ready(function() {
    var AnnouncementsView = MessagesView.extend({
        enable_refresh: false,
        no_message_template_name: "#noAnnouncementsTemplate",
        additional_filter_parameters: {message_type : "A"},
        enable_infinite_scroll: false
    });
    window.AnnouncementsView = AnnouncementsView;
});