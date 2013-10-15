$(document).ready(function() {

    var User = window.methodModel.extend({
        idAttribute: 'pk',
        url: function () {
            return '/api/users/' + this.id + "/";
        },
        methodUrl: {
            'create': '/api/users/'
        }
    });

    var Users = Backbone.Collection.extend({
        idAttribute: 'pk',
        model: User,
        url: '/api/users/'
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
            return this.model.toJSON();
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

    window.UsersView = UsersView;
});