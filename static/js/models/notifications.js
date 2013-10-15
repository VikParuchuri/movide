$(document).ready(function() {
    var Notifications = Messages.extend({
        baseUrl: '/api/notifications/?page=1',
        url: '/api/notifications/?page=1',
        comparator: function(m) {
            return -parseInt(m.get('notification_created_timestamp'));
        }
    });

    var NotificationView = MessageView.extend({
        template_name: "#notificationTemplate"
    });

    var NotificationsView = MessagesView.extend({
        collection_class: Notifications,
        view_class: NotificationView,
        enable_refresh: false,
        no_message_template_name: "#noNotificationsTemplate"
    });

    window.NotificationsView = NotificationsView;
});