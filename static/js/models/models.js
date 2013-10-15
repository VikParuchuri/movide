$(document).ready(function() {

    // Setup backbone sync to use csrf token.
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

    // Synchronous get, not AJAX.
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

    // Put CSRF token into jquery post.
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
                xhr.setRequestHeader("X-CSRFToken", CSRF_TOKEN);
            }
        }
    });

    // Jquery post functions.
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

    // Add in support for different URLs for different methods in Backbone model.
    var methodModel = Backbone.Model.extend({
        sync: function(method, model, options) {
            if (model.methodUrl && model.methodUrl[method.toLowerCase()]) {
                options = options || {};
                options.url = model.methodUrl[method.toLowerCase()];
            }
            Backbone.sync(method, model, options);
        }
    });

    // Add in support for paginating a collection via Django REST Framework and Backbone.
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
        },
        updateAll: function() {
            var collection = this;
            var options = {
                success: function(model, resp, xhr) {
                    collection.reset(model);
                }
            };
            return Backbone.sync('update', this, options);
        }
    });

    // Add in a helper function to Backbone View.
    var BaseView = Backbone.View.extend({
        destroy_view: function() {
            this.undelegateEvents();
            this.$el.removeData().unbind();
            this.remove();
            Backbone.View.prototype.remove.call(this);
        }
    });

    // Export variables.
    window.container_name = ".resource-view .resource-container";
    window.class_info = $("#classinfo");
    window.is_owner = class_info.data('is-owner');
    window.class_link = class_info.data('class-link');
    window.class_api_link = class_info.data('class-api-link');
    window.access_key = class_info.data("access-key");
    window.active_page = class_info.data("active-page");
    window.class_owner = class_info.data('class-owner');
    window.avatar_change_link = class_info.data('avatar-change-link');
    window.class_name = class_info.data('name');
    window.current_user = class_info.data('current-user');

    // Export base models.
    window.methodModel = methodModel;
    window.PaginatedCollection = PaginatedCollection;
    window.BaseView = BaseView;

    // Export functions.
    window.post_code = post_code;
    window.csrf_post = csrf_post;
    window.csrf_delete = csrf_delete;
    window.capitalize = capitalize;
});
