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

    var Tweet = Backbone.Model.extend({
        idAttribute: 'pk'
    });

    var methodModel = Backbone.Model.extend({
        sync: function(method, model, options) {
            if (model.methodUrl && model.methodUrl[method.toLowerCase()]) {
                options = options || {};
                options.url = model.methodUrl[method.toLowerCase()];
            }
            Backbone.sync(method, model, options);
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

    var Tweets = Backbone.Collection.extend({
        model: Tweet,
        url: '/api/tweets/'
    });

    var Tag = methodModel.extend({
        idAttribute: 'pk',
        url: function () {
            return '/api/tags/' + this.id;
        },
        methodUrl: {
            'create': '/api/tags/'
        }
    });

    var Tags = Backbone.Collection.extend({
        model: Tag,
        url: '/api/tags/'
    });

    var Users = Backbone.Collection.extend({
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
            this.tag = options.tag;
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

    var TagDetailView = BaseView.extend({
        el: "#dashboard-content",
        template_name: "#tagDetailTemplate",
        active: null,
        tag: null,
        options: null,
        user_view: null,
        tweet_view: null,
        events: {

        },
        initialize: function (options) {
            _.bindAll(this, 'render', 'refresh');
            this.tag = options.tag;
            this.active = options.active;
            this.options = {
                tag: this.tag,
                active: this.active
            };
        },
        base_render: function() {
            var tmpl = _.template($(this.template_name).html());
            var content_html = tmpl({tag: this.tag});
            $("#tag-sidebar").find('li').removeClass("current active");
            $(this.active).addClass("current active");
            $(this.el).html(content_html);
        },
        render: function () {
            this.base_render();
            this.user_view = new UsersView(this.options);
            this.user_view.render();
            this.tweet_view = new TweetsView(this.options);
            this.tweet_view.render();
        },
        base_refresh: function() {
            this.base_render();
        },
        refresh: function(options){
            this.tag = options.tag;
            this.active = options.active;
            this.options = {
                tag: this.tag,
                active: this.active
            };
            $(this.el).empty();
            this.base_refresh();
            this.setElement($(this.el));
            this.user_view.refresh(this.options);
            this.tweet_view.refresh(this.options);
        }
    });

    var UsersView = BaseView.extend({
        el: "#user-table",
        el_name: "#user-table",
        collection_class : Users,
        view_class: UserView,
        template_name: "#userTableTemplate",
        tag: undefined,
        active: undefined,
        events: {
            'click #create-user': 'create_user',
            'click .user-tag-delete': 'user_tag_delete'
        },
        initialize: function (options) {
            _.bindAll(this, 'render', 'renderUser', 'refresh', 'render_table', 'create_user', 'destroy_view', 'error_display', 'success_display', 'user_tag_delete');
            this.collection = new this.collection_class();
            this.tag = options.tag;
            this.active = options.active;
            this.collection.fetch({async: false, data: {tag: this.tag}});
            //this.collection.on('remove', this.refresh, this);
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
            var content_html = tmpl({content: model_html, tag: this.tag});
            $(this.el).html(content_html);
            $('#create-user').click(this.create_user);
            $('.user-tag-delete').click(this.user_tag_delete);
            return this;
        },
        renderUser: function (item) {
            var userView = new this.view_class({
                model: item,
                tag: this.tag
            });
            return userView.render().el;
        },
        refresh: function(options){
            this.tag = options.tag;
            this.collection.fetch({async:false, data: {tag: this.tag}});
            this.setElement(this.el_name);
            $(this.el).empty();
            this.render_table();
        },
        error_display: function(model, xhr, options){
            $(".create-user-form").removeClass("has-success").addClass("has-error");
            $(".help-block").html("This username cannot be validated.  Is it an actual twitter screen name?");
        },
        success_display: function(model, response, options){
            $(".create-user-form").removeClass("has-error").addClass("has-success");
            $(".help-block").html("User added!  They will now show up in the feed for this tag.");
            this.refresh({tag : this.tag});
        },
        create_user: function(event){
            event.preventDefault();
            $(event.target).attr('disabled', true);
            var user_name = $("#inputTag1").val();
            if(user_name.charAt(0)=="@"){
                user_name = user_name.substring(1,user_name.length);
            }
            var user = new User({'tag' : this.tag, 'username' : user_name});
            user.save(null,{async: false, success : this.success_display, error: this.error_display});
            $("#create-user").attr('disabled', false);
            return false;
        },
        user_tag_delete: function(event){
            event.preventDefault();
            var twitter_name = $(event.target).closest('tr').find('td.screen-name').data('screen-name');
            var item_to_remove = this.collection.where({twitter_screen_name: twitter_name})[0];
            item_to_remove.destroy({data: {tag: this.tag}, processData: true, async: false});
            this.refresh({tag : this.tag});
            return false;
        }
    });

    var TagView = BaseView.extend({
        tagName: "tr",
        className: "tags",
        template_name: "#tagTemplate",
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
            return this;
        },
        destroy: function() {
            this.model.trigger('destroy', this.model, this.model.collection, {});
        },
        remove_el: function(){
            $(this.el).remove();
        }
    });

    var TagsView = BaseView.extend({
        el: "#tags",
        tag_item_el: "#tag-content",
        collection_class : Tags,
        view_class: TagView,
        initialize: function () {
            _.bindAll(this, 'render', 'renderTag', 'renderNone', 'refresh');
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
                that.renderTag(item);
            }, this);
        },
        renderNone: function() {
            var add_tag_prompt = $("#addTagPromptTemplate").html();
            $(this.el).html(add_tag_prompt);
        },
        renderTag: function (item) {
            var tagView = new this.view_class({
                model: item
            });
            $(this.tag_item_el).append(tagView.render().el);
        },
        refresh: function(){
            this.collection.fetch({async:false});
            $(this.el).empty();
            this.render_dash();
        }
    });

    var TagSidebarView = TagView.extend({
        tagName: "li",
        className: "tag-list-item",
        template_name: "#sidebarItemTemplate"
    });

    var TagsSidebarView = TagsView.extend({
        el: "#tag-sidebar",
        view_class: TagSidebarView,
        detail_view: undefined,
        events: {
            'click #refresh-sidebar': 'refresh',
            'click .tag-name' : 'render_tag_name'
        },
        render_sidebar: function(){
            $('.tag-name', this.el).remove();
            var that = this;
            _.each(this.collection.models, function (item) {
                that.renderTag(item);
            }, this);
        },
        refresh: function(event){
            event.preventDefault();
            this.collection.fetch({async:false});
            this.render_sidebar();
            return false;
        },
        render_tag_name: function(event){
            event.preventDefault();
            var options = {
                tag: $(event.target).data('tag-name'),
                active: $(event.target).parent()
            };
            if(this.detail_view!=undefined){
                this.detail_view.refresh(options);
            } else {
                this.detail_view = new TagDetailView(options);
                this.detail_view.render();
            }
            return false;
        },
        renderTag: function (item) {
            var tagView = new this.view_class({
                model: item
            });
            $(this.el).append(tagView.render().el);
        }
    });

    var TweetView = BaseView.extend({
        tagName: "div",
        className: "tweets",
        events: {
        },
        initialize: function(){
            _.bindAll(this, 'render'); // every function that uses 'this' as the current object should be in here
            this.model.bind('change', this.render);
            this.model.bind('remove', this.unrender);
        },
        get_model_json: function(){
            var model_json = this.model.toJSON();
            model_json.created_at = model_json.created_at.split("T")[0];
            return model_json;
        },
        render: function () {
            var tmpl = _.template($("#tweetTemplate").html());
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

    var TweetsView = BaseView.extend({
        el: "#tweets",
        el_name: "#tweets",
        collection_class : Tweets,
        view_class: TweetView,
        template_name: "#tweetsTemplate",
        tag: undefined,
        initialize: function (options) {
            _.bindAll(this, 'render', 'renderTweet', 'refresh', 'render_tweets', 'destroy_view');
            this.collection = new this.collection_class();
            this.tag = options.tag;
            this.collection.fetch({async: false, data: {tag: this.tag}});
        },
        render_tweets: function(){
            this.render();
        },
        render: function () {
            var model_html = "";
            var that = this;
            if(this.collection.length > 0){
                _.each(this.collection.models, function (item) {
                    model_html = model_html + $(that.renderTweet(item)).html();
                }, this);
            } else {
                var no_tmpl = _.template($("#noTweetsTemplate").html());
                model_html = no_tmpl({tag: this.tag});
            }
            var tmpl = _.template($(this.template_name).html());
            var content_html = tmpl({tweets: model_html, tag: this.tag});
            $(this.el).html(content_html);
        },
        renderTweet: function (item) {
            var userView = new this.view_class({
                model: item
            });
            return userView.render().el;
        },
        refresh: function(options){
            this.tag = options.tag;
            this.collection.fetch({async:false, data: {tag: this.tag}});
            this.setElement(this.el_name);
            $(this.el).empty();
            this.render_tweets();
        }
    });

    window.TweetsView = TweetsView;
    window.TweetView = TweetView;
    window.TagView = TagView;
    window.TagsView = TagsView;
    window.Tag = Tag;
    window.TagSidebarView = TagSidebarView;
    window.TagsSidebarView = TagsSidebarView;
});
