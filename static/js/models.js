$(document).ready(function() {
    var CSRF_TOKEN = $('meta[name="csrf-token"]').attr('content');
    var oldSync = Backbone.sync;
    Backbone.sync = function(method, model, options){
        options.beforeSend = function(xhr){
            xhr.setRequestHeader('X-CSRFToken', CSRF_TOKEN);
        };
        return oldSync(method, model, options);
    };

    function csrfSafeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }
    function sameOrigin(url) {
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            !(/^(\/\/|http:|https:).*/.test(url));
    }

    var class_info = $("#classinfo");
    var is_owner = class_info.data('is-owner');
    var class_link = class_info.data('class-link');
    var access_key = class_info.data("access-key");
    var active_page = class_info.data("active-page");
    var class_owner = class_info.data('class-owner');
    var avatar_change_link = class_info.data('avatar-change-link');
    var class_name = class_info.data('name');

    jQuery.extend({
        getValues: function(url, data) {
            var result = null;
            $.ajax({
                url: url,
                type: 'get',
                async: false,
                data: data,
                success: function(data) {
                    result = data;
                }
            });
            return result;
        }
    });

    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
                xhr.setRequestHeader("X-CSRFToken", CSRF_TOKEN);
            }
        }
    });

    function post_code(data, success, error){
        $.ajax({
            type: "POST",
            url: "/verify_code/",
            data: data,
            success: success,
            error: error
        });
    }

    function csrf_post(url, data, success, error){
        $.ajax({
            type: "POST",
            url: url,
            data: data,
            success: success,
            error: error
        });
    }

    function csrf_delete(url, data, success, error){
        $.ajax({
            type: "DELETE",
            url: url,
            data: data,
            success: success,
            error: error
        });
    }

    function capitalize(string)
    {
        return string.charAt(0).toUpperCase() + string.slice(1);
    }

    function endsWith(str, suffix) {
        return str.indexOf(suffix, str.length - suffix.length) !== -1;
    }

    function trim1 (str) {
        return str.replace(/^\s\s*/, '').replace(/\s\s*$/, '');
    }

    function get_message_notifications(data, success, error){
        $.ajax({
            url: "/api/messages/notifications/",
            data: data,
            success: success,
            error: error
        });
    }

    var methodModel = Backbone.Model.extend({
        sync: function(method, model, options) {
            if (model.methodUrl && model.methodUrl[method.toLowerCase()]) {
                options = options || {};
                options.url = model.methodUrl[method.toLowerCase()];
            }
            Backbone.sync(method, model, options);
        }
    });

    var PaginatedCollection = Backbone.Collection.extend({
        max_time: undefined,
        initialize: function() {
            _.bindAll(this, 'parse', 'nextPage', 'previousPage');
            typeof(options) != 'undefined' || (options = {});
        },
        fetch: function(options) {
            typeof(options) != 'undefined' || (options = {});
            this.trigger("fetching");
            var self = this;
            var success = options.success;
            options.success = function(resp) {
                self.trigger("fetched");
                if(success) { success(self, resp); }
            };
            return Backbone.Collection.prototype.fetch.call(this, options);
        },
        parse: function(resp) {
            this.next = resp.next;
            this.prev = resp.previous;
            var max_timestamp = _.max(resp.results, function(r){return parseInt(r.created_timestamp);});
            if(this.max_time == undefined || max_timestamp.created_timestamp > this.max_time){
                this.max_time = max_timestamp.created_timestamp;
            }
            return resp.results;
        },
        nextPage: function(options) {
            if (this.next == undefined || this.next == null) {
                return false;
            }
            this.url = this.next;
            return this.fetch(options);
        },
        previousPage: function(options) {
            if (this.prev == undefined || this.prev == null) {
                return false;
            }
            this.url = this.prev;
            return this.fetch(options);
        }

    });

    var ClassgroupStats = methodModel.extend({
        idAttribute: 'pk',
        url: function () {
            return '/api/classes/' + this.get('name') + "/stats/";
        }
    });

    var Message = methodModel.extend({
        idAttribute: 'pk',
        url: function () {
            return '/api/messages/' + this.id + "/";
        },
        methodUrl: {
            'create': '/api/messages/'
        },
        defaults: {
            notification_text: "",
            notification_created_formatted: ""
        }
    });

    var Resource = methodModel.extend({
        idAttribute: 'pk',
        url: function () {
            return '/api/resources/' + this.id + "/";
        },
        methodUrl: {
            'create': '/api/resources/'
        }
    });

    var Resources = PaginatedCollection.extend({
        idAttribute: 'pk',
        model: Resource,
        baseUrl: '/api/resources/?page=1',
        url: '/api/resources/?page=1',
        comparator: function(m) {
            return -parseInt(m.get('created_timestamp'));
        }
    });

    var Skill = methodModel.extend({
        idAttribute: 'pk',
        url: function () {
            return '/api/skills/' + this.id + "/";
        },
        methodUrl: {
            'create': '/api/skills/'
        }
    });

    var Skills = PaginatedCollection.extend({
        idAttribute: 'pk',
        model: Skill,
        baseUrl: '/api/skills/?page=1',
        url: '/api/skills/?page=1',
        comparator: function(m) {
            return -parseInt(m.get('created_timestamp'));
        }
    });

    var EmailSubscription = methodModel.extend({
        idAttribute: 'pk',
        url: function () {
            return '/api/subscribe/' + this.id + "/";
        },
        methodUrl: {
            'create': '/api/subscribe/'
        }
    });

    var Rating = methodModel.extend({
        idAttribute: 'pk',
        url: '/api/ratings/'
    });


    var User = methodModel.extend({
        idAttribute: 'pk',
        url: function () {
            return '/api/users/' + this.id + "/";
        },
        methodUrl: {
            'create': '/api/users/'
        }
    });

    var Messages = PaginatedCollection.extend({
        idAttribute: 'pk',
        model: Message,
        baseUrl: '/api/messages/?page=1',
        url: '/api/messages/?page=1',
        comparator: function(m) {
            return -parseInt(m.get('created_timestamp'));
        }
    });

    var Notifications = Messages.extend({
        baseUrl: '/api/notifications/?page=1',
        url: '/api/notifications/?page=1',
        comparator: function(m) {
            return -parseInt(m.get('notification_created_timestamp'));
        }
    });

    var ChildMessages = Backbone.Collection.extend({
        idAttribute: 'pk',
        model: Message,
        url: '/api/messages/'
    });

    var Class = methodModel.extend({
        idAttribute: 'pk',
        url: function () {
            return '/api/classes/' + this.get('name') + "/";
        },
        methodUrl: {
            'create': '/api/classes/'
        }
    });

    var Classes = Backbone.Collection.extend({
        idAttribute: 'pk',
        model: Class,
        url: '/api/classes/'
    });

    var Users = Backbone.Collection.extend({
        idAttribute: 'pk',
        model: User,
        url: '/api/users/'
    });

    var BaseView = Backbone.View.extend({
        destroy_view: function() {
            this.undelegateEvents();
            this.$el.removeData().unbind();
            this.remove();
            Backbone.View.prototype.remove.call(this);
        }
    });

    var UserView = BaseView.extend({
        tagName: "tr",
        className: "users",
        template_name: "#userTemplate",
        tag: null,
        events: {
        },
        initialize: function(options){
            _.bindAll(this, 'render'); // every function that uses 'this' as the current object should be in here
            this.classgroup = options.classgroup;
            this.model.bind('change', this.render);
            this.model.bind('remove', this.unrender);
        },
        get_model_json: function(){
            var model_json = this.model.toJSON();
            return model_json;
        },
        render: function () {
            var tmpl = _.template($(this.template_name).html());
            var model_json = this.get_model_json();
            model_json.is_owner = is_owner;
            var model_html = tmpl(model_json);

            $(this.el).html(model_html);
            return this;
        },
        destroy: function() {
            this.model.trigger('destroy', this.model, this.model.collection, {});
        },
        remove_el: function(){
            $(this.el).remove();
        }
    });

    var StatsView = BaseView.extend({
        el: "#stats-container",
        el_name: "#stats-container",
        chart_tag: "message-chart",
        network_chart_tag: "student-network-chart",
        events: {
        },
        initialize: function (options) {
            _.bindAll(this, 'render', 'create_daily_activity_chart', 'create_network_chart', 'render_charts');
            this.classgroup = options.classgroup;
            this.display_tag = options.display_tag;
            this.options = {
                classgroup: this.classgroup,
                display_tag: this.display_tag
            };
            this.render();
        },
        render: function(){
             var class_stats = new ClassgroupStats({name : this.classgroup});
             class_stats.fetch({success: this.render_charts, error: this.render_charts_error});
        },
        render_charts: function(model, success, options){
            var messages_by_day = [];
            var messages_by_day_data = model.get('message_count_by_day');
            for (var i = 0; i < messages_by_day_data.length; i++) {
                messages_by_day.push({created: messages_by_day_data[i].created_date, count: messages_by_day_data[i].created_count});
            }
            var network_info = model.get('network_info');
            if(messages_by_day.length > 1){
                this.create_daily_activity_chart(messages_by_day);
            } else {
                $("#" + this.chart_tag).html($('#noDailyActivityChartTemplate').html())
            }
            if(network_info.nodes.length > 2 && network_info.edges.length > 1){
                this.create_network_chart(network_info)
            } else {
                $("#" + this.network_chart_tag).html($('#noNetworkChartTemplate').html());
            }

        },
        create_daily_activity_chart: function(data){
            new Morris.Line({
                element: this.chart_tag,
                data: data,
                xkey: 'created',
                ykeys: ['count'],
                labels: ['# of messages']
            });
        },
        render_charts_error: function(){
            console.log("error");
        },
        create_network_chart: function(network_info){
            var sigInst = sigma.init(document.getElementById(this.network_chart_tag)).drawingProperties({
                defaultLabelColor: '#fff'
            }).graphProperties({
                    minNodeSize: 1,
                    maxNodeSize: 5,
                    minEdgeSize: 1,
                    maxEdgeSize: 5
                }).mouseProperties({
                    maxRatio: 4
                });

            var i;
            var clusters = [{
                'id': 1,
                'nodes': [],
                'color': 'rgb('+0+','+
                    0+','+
                    0+')'
            }];

            var cluster = clusters[0];
            var nodes = network_info.nodes;
            var edges = network_info.edges;
            var palette = colorbrewer.Paired[9];
            for(i=0;i<nodes.length;i++){
                var node = nodes[i];
                sigInst.addNode(node.name,{
                    'x': Math.random(),
                    'y': Math.random(),
                    'size': node.size,
                    'color': palette[(Math.random()*palette.length|0)],
                    'cluster': cluster['id'],
                    'label': node.name
                });
                cluster.nodes.push(node.name);
            }

            for(i = 0; i < edges.length; i++){
                var edge = edges[i];
                sigInst.addEdge(i,edge.start, edge.end, {'size' : 'strength'});
            }

            var greyColor = '#FFFFFF';
            sigInst.bind('overnodes',function(event){
                var nodes = event.content;
                var neighbors = {};
                sigInst.iterEdges(function(e){
                    if(nodes.indexOf(e.source)<0 && nodes.indexOf(e.target)<0){
                        if(!e.attr['grey']){
                            e.attr['true_color'] = e.color;
                            e.color = greyColor;
                            e.attr['grey'] = 1;
                        }
                    }else{
                        e.color = e.attr['grey'] ? e.attr['true_color'] : e.color;
                        e.attr['grey'] = 0;

                        neighbors[e.source] = 1;
                        neighbors[e.target] = 1;
                    }
                }).iterNodes(function(n){
                        if(!neighbors[n.id]){
                            if(!n.attr['grey']){
                                n.attr['true_color'] = n.color;
                                n.color = greyColor;
                                n.attr['grey'] = 1;
                            }
                        }else{
                            n.color = n.attr['grey'] ? n.attr['true_color'] : n.color;
                            n.attr['grey'] = 0;
                        }
                    }).draw(2,2,2);
            }).bind('outnodes',function(){
                    sigInst.iterEdges(function(e){
                        e.color = e.attr['grey'] ? e.attr['true_color'] : e.color;
                        e.attr['grey'] = 0;
                    }).iterNodes(function(n){
                            n.color = n.attr['grey'] ? n.attr['true_color'] : n.color;
                            n.attr['grey'] = 0;
                        }).draw(2,2,2);
                });

            sigInst.startForceAtlas2();
            setTimeout(function(){sigInst.stopForceAtlas2();}, 1500);
        }
    });

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
            $(this.el).html($("#notificationDetailTemplate").html());
            this.notifications_view = new NotificationsView(this.options);
        },
        render_settings: function(){
            $(this.el).html($("#settingsDetailTemplate").html());
            this.settings_view = new SettingsView(this.options);
        },
        render_resources: function(){
            $(this.el).html($("#resourceDetailTemplate").html());
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
                    $(that.el).empty();
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

    var UsersView = BaseView.extend({
        el: "#users-container",
        el_name: "#users-container",
        collection_class : Users,
        view_class: UserView,
        template_name: "#userTableTemplate",
        user_add_message: "#user-add-message",
        user_role_toggle_tag: ".user-role-toggle",
        classgroup: undefined,
        active: undefined,
        events: {
            'click .user-tag-delete': 'user_tag_delete',
            'click #user-add': 'user_add',
            'click .user-role-toggle': 'user_role_toggle'
        },
        initialize: function (options) {
            _.bindAll(this, 'render', 'renderUser', 'refresh', 'render_table',
                'destroy_view', 'user_tag_delete', 'rebind_events', 'user_add', 'display_message', 'user_role_toggle');
            this.collection = new this.collection_class();
            this.classgroup = options.classgroup;
            this.active = options.active;
            this.display_tag = options.display_tag;
            this.link = window.location.host + class_link;
            this.user_add_link = class_link + "add_user/";
            this.user_remove_link = class_link + "remove_user/";
            this.user_role_toggle_link = class_link + "user_role_toggle/";
            this.options={
                classgroup: this.classgroup,
                display_tag: this.display_tag
            };

            var that = this;
            this.collection.fetch({
                data: {classgroup: this.classgroup},
                success: function(collection){
                    that.collection = collection;
                    that.render();
                }
            });
        },
        render_table: function(){
            this.render();
        },
        render: function () {
            var model_html = "";
            var that = this;
            if(this.collection.length > 0){
                _.each(this.collection.models, function (item) {
                    model_html = model_html + $(that.renderUser(item)).html();
                }, this);
            } else {
                model_html = $("#noUserTemplate").html()
            }
            var tmpl = _.template($(this.template_name).html());
            var content_html = tmpl({
                content: model_html,
                classgroup: this.classgroup,
                display_tag: this.display_tag,
                is_owner: is_owner
            });

            $(this.el).html(content_html);
            this.rebind_events();
            return this;
        },
        rebind_events: function(){
            $('.user-tag-delete').unbind();
            $('.user-tag-delete').click(this.user_tag_delete);
            $('#user-add').unbind();
            $('#user-add').click(this.user_add);
            $(this.user_role_toggle_tag).unbind();
            $(this.user_role_toggle_tag).click(this.user_role_toggle);
        },
        display_message: function(message, success){
            this.refresh(this.options);
            var user_add_message = $(this.user_add_message);
            user_add_message.html(message);
            var user_add_form = user_add_message.closest('.form-group');
            if(success == true){
                user_add_form.removeClass('has-error').addClass('has-success');
            } else {
                user_add_form.removeClass('has-success').addClass('has-error');
            }
        },
        user_add: function(event){
            event.preventDefault();
            var user_to_add = $('.user-add-form').find("input").val();
            var that = this;
            $.ajax({
                type: "POST",
                url: this.user_add_link,
                data: {username: user_to_add},
                success: function(){
                    that.display_message("User added.", true);
                },
                error: function(){
                    that.display_message("Failed to add user.", false);
                }
            });
            return false;
        },
        renderUser: function (item) {
            var userView = new this.view_class({
                model: item,
                classgroup: this.classgroup
            });
            return userView.render().el;
        },
        refresh: function(options){
            this.classgroup = options.classgroup;
            this.display_tag = options.display_tag;
            var that=this;
            this.collection.fetch({
                    data: {classgroup: this.classgroup},
                    success: function(){
                        that.setElement(that.el_name);
                        $(that.el).empty();
                        that.render_table();
                    }
            });
        },
        user_role_toggle: function(event){
            event.preventDefault();
            var username = $(event.target).closest('tr').find('td.username').data('username');
            var that = this;
            $.ajax({
                type: "POST",
                url: this.user_role_toggle_link,
                data: {username: username},
                success: function(response){
                    that.refresh(that.options);
                },
                error: function(){
                    that.refresh(that.options);
                }
            });
            return false;
        },
        user_tag_delete: function(event){
            event.preventDefault();
            var username = $(event.target).closest('tr').find('td.username').data('username');
            var that = this;
            bootbox.confirm("Are you sure you want to delete this user?  They will be removed from the class immediately, but their posts will remain.", function(result) {
                if(result==true){
                    $.ajax({
                        type: "POST",
                        url: that.user_remove_link,
                        data: {username: username},
                        success: function(){
                            that.refresh(that.options);
                        },
                        error: function(){
                            that.refresh(that.options);
                        }
                    });
                }
            });
            return false;
        }
    });

    var ClassView = BaseView.extend({
        tagName: "tr",
        className: "classes",
        template_name: "#classTemplate",
        role: undefined,
        events: {
        },
        initialize: function(options){
            _.bindAll(this, 'render'); // every function that uses 'this' as the current object should be in here
            this.role = options.role;
            this.model.bind('change', this.render);
            this.model.bind('remove', this.unrender);
        },
        get_model_json: function(){
            var model_json = this.model.toJSON();
            model_json.modified = model_json.modified.split("T")[0];
            model_json.role = this.role;
            return model_json;
        },
        render: function () {
            var tmpl = _.template($(this.template_name).html());
            var model_json = this.get_model_json();
            var model_html = tmpl(model_json);

            $(this.el).html(model_html);
            if (window.location.pathname === model_json.link){
                $(this.el).addClass("active");
            }
            return this;
        },
        destroy: function() {
            this.model.trigger('destroy', this.model, this.model.collection, {});
        },
        remove_el: function(){
            $(this.el).remove();
        }
    });

    var ClassesView = BaseView.extend({
        el: "#classes",
        class_item_el: "#class-content",
        collection_class : Classes,
        view_class: ClassView,
        initialize: function () {
            _.bindAll(this, 'render', 'renderClass', 'renderNone', 'refresh', 'render_dash');
            this.collection = new this.collection_class();
            var that = this;
            this.collection.fetch({
                success: function(collection){
                    that.collection = collection;
                    that.render_dash();
                }
            });
        },
        render_dash: function(){
            if(this.collection.length > 0){
                this.render();
            } else{
                this.renderNone();
            }
        },
        render: function () {
            var that = this;
            _.each(this.collection.models, function (item) {
                that.renderClass(item);
            }, this);
        },
        renderNone: function() {
            var add_tag_prompt = $("#addClassPromptTemplate").html();
            $(this.el).html(add_tag_prompt);
        },
        renderClass: function (item) {
            var username = $('.class-list').data('username');
            var role;
            if(item.get('owner') == username){
                role = "Creator"
            } else {
                role = "Participant"
            }
            var tagView = new this.view_class({
                model: item,
                role: role
            });
            $(this.class_item_el).append(tagView.render().el);
        },
        refresh: function(){
            var that = this;
            this.collection.fetch({
                success: function(collection){
                    that.collection = collection;
                    $(that.class_item_el).empty();
                    that.render_dash();
                }
            });
        }
    });

    var MessageView = BaseView.extend({
        tagName: "div",
        className: "messages",
        template_name: "#messageTemplate",
        events: {
        },
        initialize: function(){
            _.bindAll(this, 'render');
            this.model.bind('change', this.render);
            this.model.bind('remove', this.unrender);
        },
        get_model_json: function(){
            var model_json = this.model.toJSON();
            model_json.created_formatted = model_json.created.replace("Z","");
            model_json.created_formatted = moment.utc(model_json.created_formatted).local().fromNow();
            model_json.written_by_owner = (class_owner == model_json.user);
            model_json.is_owner = is_owner;
            if(model_json.notification_created != undefined){
                model_json.notification_created_formatted = model_json.notification_created.replace("Z","");
                model_json.notification_created_formatted = moment.utc(model_json.notification_created_formatted).local().fromNow();
            }
            return model_json;
        },
        render: function () {
            var tmpl = _.template($(this.template_name).html());
            var model_json = this.get_model_json();
            var model_html = tmpl(model_json);

            $(this.el).html(model_html);
            return this;
        },
        destroy: function() {
            this.model.trigger('destroy', this.model, this.model.collection, {});
        },
        remove_el: function(){
            $(this.el).remove();
        }
    });

    var MessagesView = BaseView.extend({
        el: "#messages-container",
        el_name: "#messages-container",
        collection_class : Messages,
        view_class: MessageView,
        template_name: "#messagesTemplate",
        classgroup: undefined,
        view_reply_panel: '.view-reply-panel',
        reply_to_message: '.reply-to-message-button',
        start_a_discussion: '.start-a-discussion-button',
        start_a_discussion_input: '#start-a-discussion-input',
        delete_a_message: '.delete-message-button',
        like_a_message_button: '.like-message-button',
        isLoading: false,
        interval_id: undefined,
        show_more_messages_container: "#show-more-messages-container",
        show_more_messages_template: "#showMoreMessagesTemplate",
        show_more_messages_button: "#show-more-messages-button",
        autocomplete_enabled_input: ".autocomplete-enabled-input",
        stop_polling: false,
        message_count: 0,
        document_title: document.title,
        enable_refresh: true,
        no_message_template_name: "#noMessagesTemplate",
        additional_filter_parameters: undefined,
        enable_infinite_scroll: true,
        events: {
            'click .view-reply-panel': this.render_reply_panel,
            'click .reply-to-message-button': this.post_reply_to_message,
            'click .start-a-discussion-button': this.post_reply_to_message,
            'click .reply-to-message': this.handle_reply_collapse,
            'click #show-more-messages-button': this.self_refresh,
            'click .delete-message-button': this.delete_message,
            'click .like-message-button': this.like_message
        },
        initialize: function (options) {
            _.bindAll(this, 'render', 'renderMessage', 'refresh', 'render_messages',
                'destroy_view', 'render_message_replies', 'render_reply_panel', 'post_reply_to_message',
                'checkScroll', 'show_message_notification', 'self_refresh', 'delete_message', 'like_message'
            );
            this.collection = new this.collection_class();
            this.classgroup = options.classgroup;
            this.display_tag = options.display_tag;
            this.fetch_data = {classgroup: this.classgroup};
            if(this.additional_filter_parameters != undefined){
                this.fetch_data= $.extend({}, this.additional_filter_parameters, this.fetch_data)
            }
            this.link = window.location.host + class_link;
            this.autocomplete_list = JSON.parse($('#autocomplete-list').html());

            var that=this;
            this.collection.fetch({
                data: this.fetch_data,
                success: function(collection){
                    that.collection = collection;
                    that.rebind_collection();
                    that.render();
                }
            });
        },
        render_messages: function(){
            this.render();
        },
        top_level_messages: function(){
            var top_level = [];
            var i;
            var m;
            for(i=0; i<this.collection.models.length;i++){
                m = this.collection.models[i];
                var reply_to = m.get('reply_to');
                if(reply_to == null){
                    top_level.push(m);
                }
            }
            return top_level
        },
        like_message: function(event){
            event.preventDefault();
            var button = $(event.target);
            var comment = button.closest('.comment');
            var message_id = comment.data('message-id');
            var rating = new Rating({'message' : message_id, 'rating': 1});
            button.parent().attr('disabled', true);
            rating.save({}, {
                success: function(){

                }
            });
            return false;
        },
        delete_message: function(event){
            event.preventDefault();
            var that = this;
            var comment = $(event.target).closest('.comment');
            var message_id = comment.data('message-id');
            bootbox.confirm("Are you sure you want to delete this post?  You will not be able to see it afterwards.", function(result) {
                if(result==true){
                    var message = new Message({'pk' : message_id});
                    message.destroy();
                    comment.remove();
                }
            });
            return false;
        },
        post_reply_to_message: function(event){
            event.preventDefault();
            var button = $(event.target);
            var message_div = button.closest("div.message-reply");
            var reply = message_div.find("textarea").val();
            var message_reply;
            var start_discussion;
            if(message_div.data('start-discussion') == true){
                var message_type = "D";
                if(is_owner==true){
                    var checked = message_div.find('#make-discussion-announcement-input').is(":checked");
                    if(checked==true){
                        message_type = "A";
                    }
                }
                start_discussion = true;
                message_reply = new Message({text: reply, classgroup: this.classgroup,  source: 'website', message_type: message_type})
            } else {
                start_discussion = false;
                var primary_key = button.closest('.reply-panel').data('message-id');
                message_reply = new Message({reply_to : primary_key, text: reply, classgroup: this.classgroup, source: 'website'});
            }

            var reply_form = message_div.find('.reply-to-message-form');
            var message_block = message_div.find('.help-block');
            $(button).attr('disabled', true);
            var that = this;
            message_reply.save(null,{
                success : function(){
                    $(reply_form).removeClass("has-error").addClass("has-success");
                    $(message_block).html("Discussion started! You may need to reload the page to see it.");
                    $(button).attr('disabled', false);
                    if(start_discussion == true){
                        that.collection.fetch({
                            data: that.fetch_data,
                            success: function() {
                                that.rebind_events();
                            }
                        });
                    } else {
                        that.render_message_replies(primary_key);
                        that.rebind_events();
                    }
                },
                error: function(){
                    $(reply_form).removeClass("has-success").addClass("has-error");
                    $(message_block).html("There was a problem sending your message.  Please try again later.");
                    $(button).attr('disabled', false);
                }
            });

            return false;
        },
        render_message_replies: function(message_id){
            var message_replies = this.child_messages(message_id);
            var model_html;
            if(message_replies.length > 0){
                var that = this;
                model_html = "";
                _.each(message_replies, function (item) {
                    model_html = model_html + $(that.renderMessage(item)).html();
                }, this);
            } else {
                model_html = $("#noRepliesTemplate").html();
            }
            var comment_container = $('#message-replies-container-' + message_id);
            $(comment_container).html(model_html);
        },
        render_reply_panel: function(event){
            event.preventDefault();
            var parent = $(event.target).closest('.comment');
            var message_id = parent.data('message-id');
            var reply_panel = parent.find("#reply-panel-" + message_id);
            var reply_container = parent.find('#reply-to-message-' + message_id);
            var comment_container = parent.find('#message-replies-container-' + message_id);

            var is_open = reply_panel.data('is_open');
            if(is_open){
                $(reply_panel).slideUp(300);
                $(reply_container).html('');
                $(comment_container).html('');
                $(reply_panel).data('is_open', false);
            } else{
                var tmpl = _.template($("#messageReplyTemplate").html());
                var content_html = tmpl({pk: message_id});
                reply_panel.hide();
                $(reply_container).html(content_html);
                this.render_message_replies(message_id);
                this.rebind_events();
                $(reply_panel).data('is_open', true);
                $(reply_panel).slideDown(300).show();
            }
            return false;
        },
        rebind_events: function() {
            $(this.view_reply_panel).unbind();
            $(this.view_reply_panel).click(this.render_reply_panel);
            $(this.reply_to_message).unbind();
            $(this.reply_to_message).click(this.post_reply_to_message);
            $(this.delete_a_message).unbind();
            $(this.delete_a_message).click(this.delete_message);
            $(this.like_a_message_button).unbind();
            $(this.like_a_message_button).click(this.like_message);
            $(this.start_a_discussion).unbind();
            $(this.start_a_discussion).click(this.post_reply_to_message);
            $(this.autocomplete_enabled_input).autocomplete({ disabled: true });
            var autocomplete_list = this.autocomplete_list;
            $(this.autocomplete_enabled_input).autocomplete({
                source:  function(request, response) {
                    var results = $.ui.autocomplete.filter(autocomplete_list, request.term);

                    response(results.slice(0, 10));
                },
                disabled: false,
                messages: {
                    noResults: '',
                    results: function() {}
                },
                minLength: 1
            });
            $(window).unbind();
            $(window).scroll(this.checkScroll);
            $(this.show_more_messages_button).unbind();
            $(this.show_more_messages_button).click(this.self_refresh);
            if(this.enable_refresh == true){
                if(this.interval_id != undefined){
                    clearTimeout(this.interval_id);
                }
                var that = this;
                if(this.stop_polling == false){
                    this.interval_id = setTimeout(function() {
                        get_message_notifications({classgroup: that.classgroup, start_time: that.start_time()}, that.show_message_notification, undefined);
                    }, 10000);
                } else{
                    this.interval_id = undefined;
                }
            }
        },
        show_message_notification: function(data){
            var message_html = "";
            this.message_count = data.message_count;
            if(this.message_count > 0){
                var tmpl = _.template($(this.show_more_messages_template).html());
                message_html = tmpl({
                    message_count: data.message_count
                });
                document.title = "(" + this.message_count + ") " + this.document_title;
                $(this.show_more_messages_container).html(message_html);
                if(this.message_count >= 10){
                    this.stop_polling = true;
                }
            } else {
                document.title = this.document_title;
            }
            this.rebind_events();
        },
        child_messages: function(message_id){
            message_id = parseInt(message_id);
            var child_messages = new ChildMessages();
            child_messages.fetch({async: false, data: {classgroup: this.classgroup, in_reply_to_id: message_id}});
            return child_messages.models
        },
        render: function () {
            var model_html = "";
            var that = this;
            var top_level_messages = this.top_level_messages();
            if(this.collection.length > 0){
                _.each(top_level_messages, function (item) {
                    model_html = model_html + $(that.renderMessage(item)).html();
                }, this);
            } else {
                model_html = $(this.no_message_template_name).html();
            }
            var tmpl = _.template($(this.template_name).html());
            var content_html = tmpl({messages: model_html, classgroup: this.classgroup, display_tag: this.display_tag});
            $(this.el).html(content_html);
            this.rebind_events();
        },
        renderNewMessage: function(item){
            var reply_to = item.get('reply_to');
            var comment_insert;
            var first_comment = $(this.el).find(".comments").find(".comment:first");
            var first_date = new Date(first_comment.data('created'));
            var item_date = new Date(item.get('created'));
            if(reply_to == null){
                comment_insert = $(this.el).find(".comments")
            } else {
                var comment_container = $(".comment[data-message-id='" + reply_to +"'][data-contains-replies='true']");
                if(comment_container.length > 0){
                    comment_insert = comment_container.children(".message-replies-container")
                }
            }
            if(comment_insert != undefined){
                if(item_date > first_date){
                    comment_insert.prepend(this.renderMessage(item));
                } else {
                    comment_insert.append(this.renderMessage(item));
                }
            }
        },
        renderMessage: function (item) {
            var userView = new this.view_class({
                model: item
            });
            return userView.render().el;
        },
        rebind_collection: function(){
            this.collection.bind('add', this.renderNewMessage, this);
        },
        unbind_collection: function(){
            this.collection.unbind();
        },
        refresh: function(options){
            this.classgroup = options.classgroup;
            this.display_tag = options.display_tag;
            this.unbind_collection();
            this.collection.url = this.collection.baseUrl;
            var that = this;
            this.collection.fetch({
                data: this.fetch_data,
                success: function(collection){
                    that.collection = collection;
                    that.rebind_collection();
                    that.setElement(that.el_name);
                    $(that.el).empty();
                    that.render_messages();
                }
            });
        },
        self_refresh: function(){
          this.refresh(this.options);
          this.message_count = 0;
          this.stop_polling= false;
        },
        start_time: function(){
            return this.collection.max_time;
        },
        checkScroll: function () {
            var triggerPoint = 400;
            if( !this.isLoading && ($(window).scrollTop() + $(window).height() + triggerPoint) > ($("#wrap").height()) && this.enable_infinite_scroll == true ) {
                this.isLoading = true;
                var that = this;
                var status = this.collection.nextPage({
                    success: function(){
                        that.isLoading = false;
                        that.rebind_events();
                    },
                    error: function(){
                        that.isLoading = false;
                    }
                });
                if(status==false){
                    that.isLoading = false;
                }
            }
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

    var AnnouncementsView = MessagesView.extend({
        enable_refresh: false,
        no_message_template_name: "#noAnnouncementsTemplate",
        additional_filter_parameters: {message_type : "A"},
        enable_infinite_scroll: false
    });

    var SettingsView = BaseView.extend({
        el: "#settings-container",
        template_name: "#settingsTemplate",
        student_settings_template: "#studentSettingsTemplate",
        student_settings_form: "#student-settings-form",
        avatar_change_template: "#avatarChangeTemplate",
        avatar_change_form: "#avatar-change-form",
        class_settings_template: "#classSettingsTemplate",
        class_settings_form: "#class-settings-form",
        events: {
        },
        initialize: function(options){
            _.bindAll(this, 'render', 'fetch', 'rebind_events', 'render_class_settings');
            this.class_settings_link = class_link + "class_settings/";
            this.student_class_settings_link = class_link + "student_settings/";
            this.classgroup = options.classgroup;
            this.fetch();
            this.render();
        },
        fetch: function(){
            this.student_settings = $.getValues(this.student_class_settings_link, {classgroup: this.classgroup});
            this.avatar_change = $.getValues(avatar_change_link);
            this.class_settings=undefined;
            if(is_owner == true){
                this.class_settings = $.getValues(this.class_settings_link, {classgroup: this.classgroup});
            }
        },
        render_student_settings: function(){
            var tmpl = _.template($(this.student_settings_template).html());
            var settings_html = tmpl({form_html : this.student_settings});
            return settings_html;
        },
        render_avatar_change: function(){
            var tmpl = _.template($(this.avatar_change_template).html());
            var avatar_html = tmpl({avatar_html : this.avatar_change});
            return avatar_html
        },
        render_class_settings: function(){
            var tmpl = _.template($(this.class_settings_template).html());
            var settings_html = tmpl({form_html : this.class_settings, class_link: window.location.host + class_link});
            return settings_html;
        },
        render: function () {
            $(this.el).html(this.render_student_settings() + this.render_avatar_change());
            if(is_owner == true){
                $(this.el).append(this.render_class_settings());
            }
            $("label[for='id_avatar']").hide();
            this.rebind_events();
            return this;
        },
        refresh: function(){
            this.fetch();
            this.render();
        },
        rebind_events: function(){
            $(this.student_settings_form).unbind();
            $(this.avatar_change_form).unbind();
            $(this.class_settings_form).unbind();
            var that = this;
            $(this.student_settings_form).ajaxForm(function() {
                that.refresh();
                $(that.student_settings_form).find('.help-block-message').html("Successfully saved your preferences.");
            });
            $(this.avatar_change_form).ajaxForm(function() {
                that.refresh();
                $(that.avatar_change_form).find('.help-block-message').html("Updated your avatar.");
            });
            $(this.class_settings_form).ajaxForm(function() {
                that.refresh();
                $(that.class_settings_form).find('.help-block-message').html("Saved your class settings.");
            });
        },
        remove_el: function(){
            $(this.el).remove();
        }
    });

    var ResourceView = BaseView.extend({
        tagName: "div",
        className: "resources",
        template_name: "#resourceTemplate",
        events: {
        },
        initialize: function(){
            _.bindAll(this, 'render');
            this.model.bind('change', this.render);
            this.model.bind('remove', this.unrender);
        },
        get_model_json: function(){
            var model_json = this.model.toJSON();
            model_json.created_formatted = model_json.created.replace("Z","");
            model_json.created_formatted = moment.utc(model_json.created_formatted).local().fromNow();
            model_json.written_by_owner = (class_owner == model_json.user);
            model_json.is_owner = is_owner;
            return model_json;
        },
        render: function () {
            var tmpl = _.template($(this.template_name).html());
            var model_json = this.get_model_json();
            var model_html = tmpl(model_json);

            $(this.el).html(model_html);
            return this;
        },
        destroy: function() {
            this.model.trigger('destroy', this.model, this.model.collection, {});
        },
        remove_el: function(){
            $(this.el).remove();
        }
    });

    var ResourcesView = BaseView.extend({
        el: "#resources-container",
        template_name: "#resourcesTemplate",
        create_a_resource_button: "#create-a-resource-button",
        remove_resource_button: ".remove-resource-button",
        edit_resource_button: ".edit-resource-button",
        resource_modal_id: "#create-a-resource-modal",
        resource_modal_template: "#resourceModal",
        resource_author_modal_template: "#resourceAuthorModal",
        view_a_resource_modal: '.view-a-resource-modal',
        show_resource_modal_link: '.show-resource-modal-link',
        no_resources_template: '#noResourcesTemplate',
        collection_class: Resources,
        view_class: ResourceView,
        events: {
            'click #create-a-resource-button': this.create_resource,
            'click .show-resource-modal-link': this.show_resource_modal,
            'click .remove-resource-button': this.delete_resource,
            'click .edit-resource-button': this.edit_resource
        },
        initialize: function(options){
            _.bindAll(this, 'render', 'create_resource', 'rebind_events', 'show_resource_modal', 'refresh', 'delete_resource', 'edit_resource');
            this.classgroup = options.classgroup;
            this.collection = new this.collection_class();
            this.fetch_data = {classgroup: this.classgroup};
            var that = this;
            this.collection.fetch({
                data: this.fetch_data,
                success: function(collection) {
                    that.collection = collection;
                    that.render();
                }
            });
        },
        refresh: function(){
            $(this.el).empty();
            var that = this;
            this.collection.fetch({
                data: this.fetch_data,
                success: function() {
                    that.render();
                }
            });
        },
        delete_resource: function(){
            event.preventDefault();
            var that = this;
            var resource = $(event.target).closest('.resource');
            var resource_id = $(resource).data('resource-id');
            var resource_name = $(resource).data('display-name');
            bootbox.confirm("Are you sure you want to delete the resource " + resource_name + "?  You will not be able to see it afterwards.", function(result) {
                if(result==true){
                    var resource_obj = new Resource({'pk' : resource_id});
                    resource_obj.destroy();
                    resource.remove();
                }
            });
            return false;
        },
        rebind_events: function(){
            $(this.create_a_resource_button).unbind();
            $(this.create_a_resource_button).click(this.create_resource);
            $(this.remove_resource_button).unbind();
            $(this.remove_resource_button).click(this.delete_resource);
            $(this.edit_resource_button).unbind();
            $(this.edit_resource_button).click(this.edit_resource);
            $(this.show_resource_modal_link).unbind();
            $(this.show_resource_modal_link).click(this.show_resource_modal);
        },
        show_resource_modal: function(event){
            event.preventDefault();
            var resource_id = $(event.target).data('resource-id');
            var tmpl = _.template($(this.resource_modal_template).html());
            var resource = new Resource({pk: resource_id});
            resource.fetch({async: false, data:{view_type: 'user'}});
            var modal_html = tmpl({
                html: resource.get('html'),
                display_name: resource.get('display_name')
            });
            $(this.view_a_resource_modal).modal('hide');
            $(this.view_a_resource_modal).remove();
            $(this.el).append(modal_html);
            $(this.view_a_resource_modal).modal('show');
            return false;
        },
        edit_resource: function(event){
            event.preventDefault();
            var resource_id = $(event.target).closest('.resource').data('resource-id');
            var tmpl = _.template($(this.resource_author_modal_template).html());
            var resource = new Resource({pk: resource_id});
            resource.fetch({async: false, data:{view_type: 'author'}});
            var modal_html = tmpl({
                html: resource.get('html'),
                display_name: resource.get('display_name')
            });
            $(this.view_a_resource_modal).modal('hide');
            $(this.view_a_resource_modal).remove();
            $(this.el).append(modal_html);
            $(this.view_a_resource_modal).modal('show');
            var that = this;
            return false;
        },
        create_resource: function(event){
            event.preventDefault();
            var resource = new Resource({resource_type: "vertical", classgroup: class_name});
            var that = this;
            resource.save(null, {async: false, success: function(response){
                var tmpl = _.template($(that.resource_author_modal_template).html());
                var modal_html = tmpl({
                    html: resource.get('html'),
                    display_name: "New Resource"
                });
                $(that.view_a_resource_modal).modal('hide');
                $(that.view_a_resource_modal).remove();
                $(that.el).append(modal_html);
                $(that.view_a_resource_modal).modal('show');
                $(that.view_a_resource_modal).on('hidden.bs.modal', function () {
                    that.refresh();
                });
            }});
        },
        render: function () {
            var model_html = "";
            var that = this;
            if(this.collection.length > 0){
                _.each(this.collection.models, function (item) {
                    model_html = model_html + $(that.renderResource(item)).html();
                }, this);
            } else {
                model_html = $(this.no_resources_template).html();
            }
            var tmpl = _.template($(this.template_name).html());
            var content_html = tmpl({resources: model_html, classgroup: this.classgroup});
            $(this.el).html(content_html);
            this.rebind_events();
        },
        renderResource: function (item) {
            var resourceView = new this.view_class({
                model: item
            });
            return resourceView.render().el;
        }
    });

    var SkillView = BaseView.extend({
        tagName: "div",
        className: "skills",
        template_name: "#skillTemplate",
        events: {
        },
        initialize: function(){
            _.bindAll(this, 'render');
            this.model.bind('change', this.render);
            this.model.bind('remove', this.unrender);
        },
        get_model_json: function(){
            var model_json = this.model.toJSON();
            model_json.created_formatted = model_json.created.replace("Z","");
            model_json.created_formatted = moment.utc(model_json.created_formatted).local().fromNow();
            model_json.written_by_owner = (class_owner == model_json.user);
            model_json.is_owner = is_owner;
            return model_json;
        },
        render: function () {
            var tmpl = _.template($(this.template_name).html());
            var model_json = this.get_model_json();
            var model_html = tmpl(model_json);

            $(this.el).html(model_html);
            return this;
        },
        destroy: function() {
            this.model.trigger('destroy', this.model, this.model.collection, {});
        },
        remove_el: function(){
            $(this.el).remove();
        }
    });

    var SkillsView = BaseView.extend({
        el: "#skills-container",
        template_name: "#skillsTemplate",
        create_a_skill_button: "#create-a-skill-button",
        remove_skill_button: ".remove-skill-button",
        edit_skill_button: ".edit-skill-button",
        no_skills_template: '#noSkillsTemplate',
        edit_skill_container: '#edit-a-skill',
        edit_skill_template: '#editSkillTemplate',
        autocomplete_enabled_input: '.autocomplete-enabled-input',
        added_resource_template: '#skillResourceAddTemplate',
        remove_resource_button: '.resource-add-delete',
        skill_resource_container: '.skill-resource-container',
        skill_resource_template: '#skillResourceTemplate',
        show_skill_link: '.show-skill-link',
        skill_resource: '.skill-resource',
        resource_modal_template: "#resourceModal",
        view_a_resource_modal: '.view-a-resource-modal',
        show_resource_modal_link: '.show-resource-modal-link',
        collection_class: Skills,
        view_class: SkillView,
        events: {
            'click #create-a-skill-button': this.create_skill,
            'click .remove-skill-button': this.delete_skill,
            'click .edit-skill-button': this.edit_skill
        },
        initialize: function(options){
            _.bindAll(this, 'render', 'rebind_events', 'delete_skill', 'edit_skill',
                'create_skill', 'rebind_autocomplete', 'rebind_skill_save', 'save_skill',
                'add_resource', 'show_skill_display', 'show_resource_modal');
            this.classgroup = class_name;
            this.collection = new this.collection_class();
            this.fetch_data = {classgroup: this.classgroup};
            this.autocomplete_list = JSON.parse($('#autocomplete-list').html());
            var that = this;
            this.collection.fetch({
                data: this.fetch_data,
                success: function(collection) {
                    that.collection = collection;
                    that.render();
                }
            });
        },
        refresh: function(){
            $(this.el).empty();
            var that = this;
            this.collection.fetch({
                data: this.fetch_data,
                success: function() {
                    that.render();
                }
            });
        },
        show_skill_display: function(event){
            event.preventDefault();
            var skill = $(event.target).closest('.skill');
            var skill_resources = $(this.skill_resource);
            if($(skill_resources).length > 0){
                $(skill_resources).remove();
            } else {
                var skill_id = $(skill).data('skill-id');
                var skill_resource_container = $(this.skill_resource_container, skill);
                var resources = $(skill).data('resources');
                var resource_ids = $(skill).data('resource-ids');
                if(typeof(resource_ids) == "number"){
                    resource_ids = [resource_ids];
                } else {
                    resource_ids = resource_ids.split(",,");
                }

                if(typeof(resources) == "number"){
                    resources = [resources];
                } else {
                    resources = resources.split(",,");
                }

                if(typeof(resources) == "string"){
                    resources = [resources];
                }

                var tmpl = _.template($(this.skill_resource_template).html());
                var skill_html = "";
                for(var i=0;i<resources.length;i++){
                    skill_html = skill_html + tmpl({name: resources[i], id: resource_ids[i]});
                }
                $(skill_resource_container).append(skill_html);
                $(this.show_resource_modal_link).unbind();
                $(this.show_resource_modal_link).click(this.show_resource_modal);
            }
            return false;
        },
        delete_skill: function(){
            event.preventDefault();
            var skill = $(event.target).closest('.skill');
            var skill_id = $(skill).data('skill-id');
            var skill_name = $(skill).data('display-name');
            bootbox.confirm("Are you sure you want to delete the skill " + skill_name + "?  You will not be able to see it afterwards.", function(result) {
                if(result==true){
                    var skill_obj = new Skill({'pk' : skill_id});
                    skill_obj.destroy();
                    skill.remove();
                }
            });
            return false;
        },
        rebind_events: function(){
            $(this.create_a_skill_button).unbind();
            $(this.create_a_skill_button).click(this.create_skill);
            $(this.edit_skill_button).unbind();
            $(this.edit_skill_button).click(this.edit_skill);
            $(this.remove_skill_button).unbind();
            $(this.remove_skill_button).click(this.delete_skill);
            $(this.show_skill_link).unbind();
            $(this.show_skill_link).click(this.show_skill_display);
        },
        edit_skill: function(event){
            event.preventDefault();
            if($(this.edit_skill_container).length > 0 ){
                $(this.edit_skill_container).remove();
            } else {
                var skill_container = $(event.target).closest('.skill');
                var skill_id = skill_container.data('skill-id');
                var grading_policy = skill_container.data('grading-policy');
                var display_name = skill_container.data('display-name');
                var resource_text = skill_container.data('resources');
                if(typeof(resource_text) == "number"){
                    resource_text = [resource_text];
                } else {
                    resource_text = resource_text.split(",,");
                }
                var resources = "";
                var r;
                for(var i=0;i<resource_text.length;i++){
                    r = resource_text[i].toString();
                    if(r.length > 0){
                        resources = resources + this.render_added_resource(r);
                    }
                }
                var tmpl = _.template($(this.edit_skill_template).html());
                var skill_html = tmpl({
                    display_name: display_name,
                    resources: resources,
                    skill_id: skill_id,
                    save_text: "Save Skill",
                    grading_policy: grading_policy
                });
                $(skill_container).append(skill_html);
                this.rebind_autocomplete();
                this.rebind_skill_save();
            }
            return false;
        },
        save_skill: function(event){
            event.preventDefault();
            var edit_skill_container = $(event.target).closest(this.edit_skill_container);
            var skill_name = $("#skill-name-input", edit_skill_container).val();
            var grading_policy = $("#grading-policy-input :selected", edit_skill_container).attr('value');
            var added_resources = $(".added-resource", edit_skill_container);
            var resource_names = [];
            for(var i=0;i<added_resources.length;i++){
                resource_names.push($(added_resources[i]).data('name'));
            }
            var skill_id = edit_skill_container.data('skill-id');
            var skill;
            if(skill_id != ""){
                skill = new Skill({pk: skill_id, name: skill_name, resources: resource_names, classgroup: this.classgroup, grading_policy: grading_policy});
            } else {
                skill = new Skill({name: skill_name, resources: resource_names, classgroup: this.classgroup});
            }
            var that = this;
            skill.save(null, {
                success: function(){
                    $(edit_skill_container).remove();
                    that.refresh();
                },
                error: function(){
                    $(".help-block-skill", edit_skill_container).html("Could not save the skill.");
                }
            });
            return false;
        },
        create_skill: function(event){
            event.preventDefault();
            if($(this.edit_skill_container).length > 0 ){
                $(this.edit_skill_container).remove();
            } else {
                var tmpl = _.template($(this.edit_skill_template).html());
                $(this.el).prepend(tmpl({
                    display_name: "",
                    resources: "",
                    skill_id: "",
                    save_text: "Create Skill",
                    grading_policy: "COM"
                }));
                this.rebind_autocomplete();
                this.rebind_skill_save();
            }
            return false;
        },
        render: function () {
            var model_html = "";
            var that = this;
            if(this.collection.length > 0){
                _.each(this.collection.models, function (item) {
                    model_html = model_html + $(that.renderSkill(item)).html();
                }, this);
            } else {
                model_html = $(this.no_skills_template).html();
            }
            var tmpl = _.template($(this.template_name).html());
            var content_html = tmpl({skills: model_html, classgroup: this.classgroup});
            $(this.el).html(content_html);
            this.rebind_events();
        },
        rebind_skill_save: function(){
            $(this.edit_skill_container + " button[type='submit']").unbind();
            $(this.edit_skill_container + " button[type='submit']").click(this.save_skill);
            $(this.edit_skill_container + " .add-resource-button").unbind();
            $(this.edit_skill_container + " .add-resource-button").click(this.add_resource);
            $(this.remove_resource_button).unbind();
            $(this.remove_resource_button).click(this.remove_resource);
        },
        add_resource: function(event){
            event.preventDefault();
            var form_group = $(event.target).closest('.form-group');
            var name = $('#resource-name-input', form_group).val();
            $(form_group).append(this.render_added_resource(name));
            $(this.remove_resource_button).unbind();
            $(this.remove_resource_button).click(this.remove_resource);
            $('#resource-name-input', form_group).val('');
            return false;
        },
        remove_resource: function(event){
            event.preventDefault();
            var added_resource = $(event.target).closest('.added-resource');
            added_resource.remove();
            return false;
        },
        render_added_resource: function(name){
            var tmpl = _.template($(this.added_resource_template).html());
            return tmpl({
                name: name
            })
        },
        show_resource_modal: function(event){
            event.preventDefault();
            var resource_id = $(event.target).closest('.skill-resource').data('id');
            var tmpl = _.template($(this.resource_modal_template).html());
            var resource = new Resource({pk: resource_id});
            resource.fetch({async: false, data:{view_type: 'user'}});
            var modal_html = tmpl({
                html: resource.get('html'),
                display_name: resource.get('display_name')
            });
            $(this.view_a_resource_modal).modal('hide');
            $(this.view_a_resource_modal).remove();
            $(this.el).append(modal_html);
            $(this.view_a_resource_modal).modal('show');
            return false;
        },
        rebind_autocomplete: function(){
            $(this.autocomplete_enabled_input).autocomplete({ disabled: true });
            var autocomplete_list = this.autocomplete_list;
            var resource_names = [];
            for (var i = 0; i < autocomplete_list.length; i++) {
                if(autocomplete_list[i].charAt(0) == "*"){
                    resource_names.push(autocomplete_list[i].replace("*",""));
                }
            }
            $(this.autocomplete_enabled_input).autocomplete({
                source:  function(request, response) {
                    var results = $.ui.autocomplete.filter(resource_names, request.term);
                    response(results.slice(0, 10));
                },
                disabled: false,
                messages: {
                    noResults: '',
                    results: function() {}
                },
                minLength: 1
            });
        },
        renderSkill: function (item) {
            var skillView = new this.view_class({
                model: item
            });
            return skillView.render().el;
        }
    });

    function extractLast( term ) {
        return split( term ).pop();
    }
    function split( val ) {
        return val.split( /,\s*/ );
    }

    window.MessagesView = MessagesView;
    window.MessageView = MessageView;
    window.ClassView = ClassView;
    window.ClassesView = ClassesView;
    window.Class = Class;
    window.EmailSubscription = EmailSubscription;
    window.ClassDetailView = ClassDetailView;
    window.post_code = post_code;
    window.csrf_post = csrf_post;
    window.csrf_delete = csrf_delete;
    window.container_name = ".resource-view .resource-container";
    window.class_name = class_name;
    window.capitalize = capitalize;
});
