$(document).ready(function() {

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

    window.SettingsView = SettingsView;
});
