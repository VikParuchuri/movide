$(document).ready(function() {

    function get_message_notifications(data, success, error){
        $.ajax({
            url: "/api/messages/notifications/",
            data: data,
            success: success,
            error: error
        });
    }

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

    var Messages = PaginatedCollection.extend({
        idAttribute: 'pk',
        model: Message,
        baseUrl: '/api/messages/?page=1',
        url: '/api/messages/?page=1',
        comparator: function(m) {
            return -parseInt(m.get('created_timestamp'));
        }
    });

    var Rating = methodModel.extend({
        idAttribute: 'pk',
        url: '/api/ratings/'
    });

    var ChildMessages = Backbone.Collection.extend({
        idAttribute: 'pk',
        model: Message,
        url: '/api/messages/'
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

    window.MessagesView = MessagesView;
    window.MessageView = MessageView;
    window.Messages = Messages;
});
