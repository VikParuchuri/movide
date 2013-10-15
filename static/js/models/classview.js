$(document).ready(function() {
    var ClassDetailView = BaseView.extend({
        el: "#dashboard-content",
        classgroup: null,
        options: null,
        user_view: null,
        message_view: null,
        tag_model: null,
        chart_tag: "message-chart",
        network_chart_tag: "student-network-chart",
        template_name: "#classDetailTemplate",
        sidebar_item_tag: ".sidebar-item",
        events: {
        },
        initialize: function (options) {
            _.bindAll(this, 'render', 'refresh', 'make_active', 'render_page', 'render_messages');
            this.classgroup = options.classgroup;
            this.display_tag = options.display_tag;
            this.options = {
                classgroup: this.classgroup,
                display_tag: this.display_tag
            };
            this.render();
        },
        make_active: function(elem){
            $("#tag-sidebar").find('li').removeClass("current active");
            $(elem).addClass("current active");
        },
        render_users: function() {
            $(this.el).html($("#usersDetailTemplate").html());
            this.user_view = new UsersView(this.options);
        },
        render_messages: function() {
            var tmpl = _.template($("#messageDetailTemplate").html());
            $(this.el).html(tmpl({
                is_owner: is_owner,
                enable_posting: this.class_model.get('class_settings').enable_posting
            }));
            this.message_view = new MessagesView(this.options);
        },
        render_stats: function() {
            $(this.el).html($("#statsDetailTemplate").html());
            this.stats_view = new StatsView(this.options);
        },
        render_notifications: function(){
            var tmpl = _.template($("#notificationDetailTemplate").html());
            $(this.el).html(tmpl(this.class_model.toJSON()));
            this.notifications_view = new NotificationsView(this.options);
            this.gradings_view = new GradingsView(this.options);
        },
        render_settings: function(){
            $(this.el).html($("#settingsDetailTemplate").html());
            this.settings_view = new SettingsView(this.options);
        },
        render_resources: function(){
            var tmpl = _.template($("#resourceDetailTemplate").html());
            $(this.el).html(tmpl({is_owner: is_owner}));
            this.resources_view = new ResourcesView(this.options);
        },
        render_home: function(){
            var tmpl = _.template($("#homeDetailTemplate").html());
            $(this.el).html(tmpl(this.class_model.toJSON()));
            this.announcements_view = new AnnouncementsView(this.options);
        },
        render_skills: function(){
            var tmpl = _.template($("#skillDetailTemplate").html());
            $(this.el).html(tmpl({
                is_owner: is_owner
            }));
            this.skills_view = new SkillsView(this.options);
        },
        render: function () {
            this.class_model = new Class({name : this.classgroup});
            var that = this;
            this.class_model.fetch({
                success: function(model){
                    that.rebind_events();
                    that.class_model = model;
                    that.render_page();
                }
            });
        },
        render_page: function(){
            if(active_page == "messages"){
                this.render_messages();
            } else if(active_page == "stats"){
                this.render_stats();
            } else if(active_page == "users"){
                this.render_users();
            } else if(active_page == "notifications"){
                this.render_notifications();
            } else if(active_page == "settings"){
                this.render_settings();
            } else if(active_page == "home"){
                this.render_home();
            } else if(active_page == "resources"){
                this.render_resources();
            } else if(active_page == "skills"){
                this.render_skills();
            }
        },
        refresh: function(){
            $(this.el).empty();
            this.render();
            this.setElement($(this.el));
        },
        rebind_events: function() {
            $(this.sidebar_item_tag).unbind();
            $(this.sidebar_item_tag).click(this.sidebar_click);
        }
    });

    window.ClassDetailView = ClassDetailView;
});