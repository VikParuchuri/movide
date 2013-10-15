$(document).ready(function() {

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

    window.SkillsView = SkillsView;
});