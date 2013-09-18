$(document).ready(function() {
    var CSRF_TOKEN = $('meta[name="csrf-token"]').attr('content');
    var oldSync = Backbone.sync;
    Backbone.sync = function(method, model, options){
        options.beforeSend = function(xhr){
            xhr.setRequestHeader('X-CSRFToken', CSRF_TOKEN);
        };
        return oldSync(method, model, options);
    };

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

    var methodModel = Backbone.Model.extend({
        sync: function(method, model, options) {
            if (model.methodUrl && model.methodUrl[method.toLowerCase()]) {
                options = options || {};
                options.url = model.methodUrl[method.toLowerCase()];
            }
            Backbone.sync(method, model, options);
        }
    });

    var Message = methodModel.extend({
        idAttribute: 'pk',
        url: function () {
            return '/api/messages/' + this.id;
        },
        methodUrl: {
            'create': '/api/messages/'
        }
    });

    var EmailSubscription = methodModel.extend({
        idAttribute: 'pk',
        url: function () {
            return '/api/subscribe/' + this.id;
        },
        methodUrl: {
            'create': '/api/subscribe/'
        }
    });


    var User = methodModel.extend({
        idAttribute: 'pk',
        url: function () {
            return '/api/users/' + this.id;
        },
        methodUrl: {
            'create': '/api/users/'
        }
    });

    var Messages = Backbone.Collection.extend({
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
        render: function(){
            var tag_information = new TagInformation({name : this.classgroup});
             tag_information.fetch({success: this.render_additional_charts, error: this.render_additional_charts_error});
             if(messages_by_day.length > 1){
             var chart_width = $("#messages").width();
             $('#' + this.chart_tag).css('width', chart_width);
                this.create_chart(messages_by_day);
             }
        },
        create_chart: function(data){
            new Morris.Line({
                element: this.chart_tag,
                data: data,
                xkey: 'created',
                ykeys: ['count'],
                labels: ['# of messages']
            });
        },
        render_additional_charts_error: function(){
            console.log("error");
        },
        render_additional_charts: function(model, success, options){
            $("#student-network-chart").empty();
            if(model.get('network_info').nodes.length < 2 || model.get('network_info').edges.length < 1){
                $("#student-network-chart").html($('#noNetworkChartTemplate').html());
                return
            }
            $('a[href="#stats-container"]').on('shown.bs.tab', function (e) {
                var sigInst = sigma.init(document.getElementById("student-network-chart")).drawingProperties({
                    defaultLabelColor: '#fff'
                }).graphProperties({
                        minNodeSize: 0.5,
                        maxNodeSize: 5,
                        minEdgeSize: 1,
                        maxEdgeSize: 1
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
                var nodes = model.get('network_info').nodes;
                var edges = model.get('network_info').edges;
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
                $('a[href="#stats-container"]').unbind();
            });
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
            'click.sidebar-item': this.sidebar_click
        },
        initialize: function (options) {
            _.bindAll(this, 'render', 'refresh', 'make_active', 'sidebar_click');
            this.classgroup = options.classgroup;
            this.display_tag = options.display_tag;
            this.options = {
                classgroup: this.classgroup,
                display_tag: this.display_tag
            };
        },
        make_active: function(elem){
            $("#tag-sidebar").find('li').removeClass("current active");
            $(elem).addClass("current active");
        },
        base_render: function() {
            this.class_model = new Class({name : this.classgroup});
            this.class_model.fetch({async: false});
            $(this.el).html("");
            this.rebind_events();
        },
        sidebar_click: function(event){
            var target = $(event.target);
            var name = target.data('name');

            if(name === "stats"){
                this.render_stats();
            } else if(name === "messages"){
                this.render_messages();
            } else if(name=== "users"){
                this.render_users();
            }
            this.make_active(target.closest('li'));
        },
        render_users: function() {
            this.refresh();
            $(this.el).html($("#usersDetailTemplate").html());
            this.user_view = new UsersView(this.options);
            this.user_view.render();
        },
        render_messages: function() {
            this.refresh();
            $(this.el).html($("#messageDetailTemplate").html());
            this.message_view = new MessagesView(this.options);
            this.message_view.render();
        },
        render_stats: function() {
            this.refresh();
            $(this.el).html($("#statsDetailTemplate").html());
            this.stats_view = new StatsView(this.options);
            this.stats_view.render();
        },
        render: function () {
            this.base_render();
            this.render_messages();
        },
        refresh: function(){
            $(this.el).empty();
            this.base_render();
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
        classgroup: undefined,
        active: undefined,
        events: {
            'click .user-tag-delete': 'user_tag_delete'
        },
        initialize: function (options) {
            _.bindAll(this, 'render', 'renderUser', 'refresh', 'render_table', 'destroy_view', 'user_tag_delete');
            this.collection = new this.collection_class();
            this.classgroup = options.classgroup;
            this.active = options.active;
            this.display_tag = options.display_tag;
            this.collection.fetch({async: false, data: {classgroup: this.classgroup}});
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
            var content_html = tmpl({content: model_html, classgroup: this.classgroup, display_tag: this.display_tag});
            $(this.el).html(content_html);
            $('.user-tag-delete').unbind();
            $('.user-tag-delete').click(this.user_tag_delete);
            return this;
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
            this.collection.fetch({async:false, data: {classgroup: this.classgroup}});
            this.setElement(this.el_name);
            $(this.el).empty();
            this.render_table();
        },
        user_tag_delete: function(event){
            event.preventDefault();
            var twitter_name = $(event.target).closest('tr').find('td.screen-name').data('screen-name');
            var item_to_remove = this.collection.where({twitter_screen_name: twitter_name})[0];
            item_to_remove.destroy({data: {classgroup: this.classgroup}, processData: true, async: false});
            this.refresh({classgroup : this.classgroup});
            return false;
        }
    });

    var ClassView = BaseView.extend({
        tagName: "tr",
        className: "classes",
        template_name: "#classTemplate",
        events: {
        },
        initialize: function(){
            _.bindAll(this, 'render'); // every function that uses 'this' as the current object should be in here
            this.model.bind('change', this.render);
            this.model.bind('remove', this.unrender);
        },
        get_model_json: function(){
            var model_json = this.model.toJSON();
            model_json.modified = model_json.modified.split("T")[0];
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
            _.bindAll(this, 'render', 'renderClass', 'renderNone', 'refresh');
            this.collection = new this.collection_class();
            this.collection.fetch({async:false});
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
            var tagView = new this.view_class({
                model: item
            });
            $(this.class_item_el).append(tagView.render().el);
        },
        refresh: function(){
            this.collection.fetch({async:false});
            $(this.class_item_el).empty();
            this.render_dash();
        }
    });

    var MessageView = BaseView.extend({
        tagName: "div",
        className: "messages",
        events: {
        },
        initialize: function(){
            _.bindAll(this, 'render');
            this.model.bind('change', this.render);
            this.model.bind('remove', this.unrender);
        },
        get_model_json: function(){
            var model_json = this.model.toJSON();
            model_json.created = model_json.created.replace("Z","");
            model_json.created = moment.utc(model_json.created).local().calendar();
            return model_json;
        },
        render: function () {
            var tmpl = _.template($("#messageTemplate").html());
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
        view_message_replies_tag: '.view-message-replies',
        reply_to_message: '.reply-to-message-button',
        start_a_discussion: '.start-a-discussion-button',
        open_reply_panel: '.reply-to-message',
        events: {
            'click .view-message-replies': this.render_message_replies,
            'click .reply-to-message-button': this.post_reply_to_message,
            'click .start-a-discussion-button': this.post_reply_to_message
        },
        initialize: function (options) {
            _.bindAll(this, 'render', 'renderMessage', 'refresh', 'render_messages', 'destroy_view', 'render_message_replies', 'post_reply_to_message');
            this.collection = new this.collection_class();
            this.classgroup = options.classgroup;
            this.display_tag = options.display_tag;
            this.collection.fetch({async: false, data: {classgroup: this.classgroup}});
            this.rebind_collection();
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
        handle_reply_collapse: function(event){
          event.preventDefault();
        },
        post_reply_to_message: function(event){
            event.preventDefault();
            var button = $(event.target);
            var message_div = button.closest("div.message-reply");
            var reply = message_div.find("input").val();
            if(message_div.data('start_discussion') == true){
                var message_reply = new Message({text: reply, classgroup: this.classgroup})
            } else {
                var primary_key = button.data('primary-key');
                var message_reply = new Message({reply_to : primary_key, text: reply, classgroup: this.classgroup, source: 'website'});
            }

            var reply_form = message_div.find('.reply-to-message-form');
            var message_block = message_div.find('.help-block');
            $(button).attr('disabled', true);
            var that = this;
            message_reply.save(null,{
                success : function(){
                    $(reply_form).removeClass("has-error").addClass("has-success");
                    $(message_block).html("Discussion started!");
                    $(button).attr('disabled', false);
                    that.collection.fetch({async: false, data: {classgroup: that.classgroup}});
                },
                error: function(){
                    $(reply_form).removeClass("has-success").addClass("has-error");
                    $(message_block).html("There was a problem sending your message.  Please try again later.");
                    $(button).attr('disabled', false);
                }
            });

            return false;
        },
        render_message_replies: function(event){
            event.preventDefault();
            var message_id = $(event.target).parent().data('message-id');
            var comment_container = $(event.target).parent().find('#message-replies-container-' + message_id);
            if(!comment_container.data('contains-replies')){
                var message_replies = this.child_messages(message_id);
                if(message_replies.length > 0){
                    var that = this;
                    var model_html = "";
                    _.each(message_replies, function (item) {
                        model_html = model_html + $(that.renderMessage(item)).html();
                    }, this);
                    var tmpl = _.template($(this.template_name).html());
                    var content_html = tmpl({messages: model_html, classgroup: this.classgroup, display_tag: this.display_tag});
                    $(comment_container).html(content_html).hide().slideDown(300);
                    comment_container.data('contains-replies', true);
                    this.rebind_events();
                } else {
                    var no_replies = $("#noRepliesTemplate").html();
                    $(comment_container).html(no_replies);
                }
            } else {
                $(comment_container).slideUp(300).html('');
                comment_container.data('contains-replies', false);
            }
            return false;
        },
        rebind_events: function() {
            $(this.view_message_replies_tag).unbind();
            $(this.view_message_replies_tag).click(this.render_message_replies);
            $(this.reply_to_message).unbind();
            $(this.reply_to_message).click(this.post_reply_to_message);
            $(this.start_a_discussion).unbind();
            $(this.start_a_discussion).click(this.post_reply_to_message);
            $(this.open_reply_panel).unbind();
            $(this.open_reply_panel).click(this.handle_reply_collapse);
        },
        child_messages: function(message_id){
            message_id = parseInt(message_id);
            var children = [];
            var i;
            var m;
            for(i=0; i<this.collection.models.length;i++){
                m = this.collection.models[i];
                var reply_to = parseInt(m.get('reply_to'));
                if(reply_to == message_id){
                    children.push(m);
                }
            }
            return children
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
                var no_tmpl = _.template($("#noMessagesTemplate").html());
                model_html = no_tmpl({classgroup: this.classgroup, display_tag: this.display_tag});
            }
            var tmpl = _.template($(this.template_name).html());
            var content_html = tmpl({messages: model_html, classgroup: this.classgroup, display_tag: this.display_tag});
            $(this.el).html(content_html);
            this.rebind_events();
        },
        renderNewMessage: function(item){
            var reply_to = item.get('reply_to');
            if(reply_to == null){
                $(this.el).find(".comments").prepend(this.renderMessage(item));
            } else {
                var comment_container = $(".comment[data-message-id='" + reply_to +"']");
                if(comment_container.length > 0){
                    comment_container.children(".message-replies-container").prepend(this.renderMessage(item));
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
            this.collection.fetch({async:false, data: {classgroup: this.classgroup}});
            this.rebind_collection();
            this.setElement(this.el_name);
            $(this.el).empty();
            this.render_messages();
        }
    });

    window.MessagesView = MessagesView;
    window.MessageView = MessageView;
    window.ClassView = ClassView;
    window.ClassesView = ClassesView;
    window.Class = Class;
    window.EmailSubscription = EmailSubscription;
    window.ClassDetailView = ClassDetailView;
});
