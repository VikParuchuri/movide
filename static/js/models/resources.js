$(document).ready(function() {

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
            return m.get('priority');
        }
    });

    var Section = methodModel.extend({
        idAttribute: 'pk',
        url: function () {
            return '/api/sections/' + this.id + "/";
        },
        methodUrl: {
            'create': '/api/sections/'
        }
    });

    var Sections = Backbone.Collection.extend({
        idAttribute: 'pk',
        model: Section,
        url: '/api/sections/'
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
            model_json.current_user = current_user;
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

    var SectionView = ResourceView.extend({
        tagName: "div",
        className: "sections",
        template_name: "#sectionTemplate",
        get_model_json: function(){
            var model_json = this.model.toJSON();
            model_json.created_formatted = model_json.created.replace("Z","");
            model_json.created_formatted = moment.utc(model_json.created_formatted).local().fromNow();
            model_json.is_owner = is_owner;
            return model_json;
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
        show_section_resources_link: '.show-section-resources',
        no_resources_template: '#noResourcesTemplate',
        no_sections_template: '#noSectionsTemplate',
        edit_section_container: '#edit-a-section',
        create_section_button: '#create-a-section-button',
        edit_section_template: '#editSectionTemplate',
        remove_section_button: ".remove-section-button",
        edit_section_button: ".edit-section-button",
        no_section_resources_template: "#noSectionResourcesTemplate",
        sortable_list_elem: ".sortable",
        section_view_class: SectionView,
        section_collection_class: Sections,
        collection_class: Resources,
        view_class: ResourceView,
        events: {
            'click #create-a-resource-button': this.create_resource,
            'click .show-resource-modal-link': this.show_resource_modal,
            'click .remove-resource-button': this.delete_resource,
            'click .edit-resource-button': this.edit_resource
        },
        initialize: function(options){
            _.bindAll(this, 'render', 'create_resource', 'rebind_events', 'show_resource_modal',
                'refresh', 'delete_resource', 'edit_resource', 'create_section', 'save_section',
                'delete_section', 'edit_section', 'show_section_resources', 'refetch', 'update_order',
                'rebind_resource_buttons');
            this.classgroup = options.classgroup;
            this.collection = new this.collection_class();
            this.section_collection = new this.section_collection_class();
            this.fetch_data = {classgroup: this.classgroup};
            this.refetch();
        },
        refetch: function(){
            var that = this;
            this.section_collection.fetch({
                data: this.fetch_data,
                async: false
            });
            this.collection.fetch({
                data: this.fetch_data,
                success: function(collection) {
                    that.render();
                }
            });
        },
        refresh: function(){
            $(this.el).empty();
            this.refetch();
        },
        create_section: function(event){
            event.preventDefault();
            if($(this.edit_section_container).length > 0 ){
                $(this.edit_section_container).remove();
            } else {
                var tmpl = _.template($(this.edit_section_template).html());
                $(this.el).prepend(tmpl({
                    display_name: "",
                    resources: "",
                    section_id: "",
                    save_text: "Create Section"
                }));
                this.rebind_section_save();
            }
            return false;
        },
        delete_section: function(){
            event.preventDefault();
            var that = this;
            var section = $(event.target).closest('.section');
            var section_id = $(section).data('section-id');
            var section_name = $(section).data('display-name');
            bootbox.confirm("Are you sure you want to delete the section " + section_name + "?  You will not be able to see it afterwards.  Removing a section will not remove any resources in it.  They will go back to the unorganized resources list.", function(result) {
                if(result==true){
                    var section_obj = new Section({'pk' : section_id});
                    section_obj.destroy();
                    section.remove();
                }
            });
            return false;
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
        edit_section: function(event){
            event.preventDefault();
            if($(this.edit_section_container).length > 0 ){
                $(this.edit_section_container).remove();
            } else {
                var section = $(event.target).closest('.section');
                var section_id = section.data('section-id');
                var display_name = section.data('display-name');
                var tmpl = _.template($(this.edit_section_template).html());
                var section_html = tmpl({
                    display_name: display_name,
                    section_id: section_id,
                    save_text: "Save Section"
                });
                section.append(section_html);
                this.rebind_section_save();
            }
            return false;
        },
        save_section: function(event){
            event.preventDefault();
            var edit_section_container = $(event.target).closest(this.edit_section_container);
            var section_name = $("#section-name-input", edit_section_container).val();
            var section_id = edit_section_container.data('section-id');
            var section;
            if(section_id != ""){
                section = new Section({pk: section_id, name: section_name, classgroup: this.classgroup});
            } else {
                section = new Section({name: section_name, classgroup: this.classgroup});
            }
            var that = this;
            section.save(null, {
                success: function(){
                    $(edit_section_container).remove();
                    that.refresh();
                },
                error: function(){
                    $(".help-block-section", edit_section_container).html("Could not save the section.");
                }
            });
            return false;
        },
        rebind_section_save: function(){
            $(this.edit_section_container + " button[type='submit']").unbind();
            $(this.edit_section_container + " button[type='submit']").click(this.save_section);
        },
        rebind_resource_buttons: function(){
            $(this.remove_resource_button).unbind();
            $(this.remove_resource_button).click(this.delete_resource);
            $(this.edit_resource_button).unbind();
            $(this.edit_resource_button).click(this.edit_resource);
            $(this.show_resource_modal_link).unbind();
            $(this.show_resource_modal_link).click(this.show_resource_modal);
        },
        rebind_events: function(){
            $(this.create_a_resource_button).unbind();
            $(this.create_a_resource_button).click(this.create_resource);
            this.rebind_resource_buttons();
            $(this.create_section_button).unbind();
            $(this.create_section_button).click(this.create_section);
            $(this.remove_section_button).unbind();
            $(this.remove_section_button).click(this.delete_section);
            $(this.edit_section_button).unbind();
            $(this.edit_section_button).click(this.edit_section);
            if(is_owner == true){
                $(this.sortable_list_elem).unbind();
                var that = this;
                $(this.sortable_list_elem).sortable({
                    connectWith: this.sortable_list_elem,
                    placeholder: "ui-state-highlight",
                    helper:'clone',
                    axis: 'y',
                    delay: 150,
                    update: function( event, ui ) {
                        that.update_order(event);
                    },
                    items: ".resource",
                    handle: ".drag-handle"
                })
            }
            $(this.show_section_resources_link).unbind();
            $(this.show_section_resources_link).click(this.show_section_resources)
        },
        show_section_resources: function(event){
            event.preventDefault();
            var section = $(event.target).closest('.section');
            var name = section.data('name');
            var resource_container = section.find('.section-resources');
            var resources = resource_container.find('.resource');
            if(resources.length > 0){
                resource_container.empty();
            } else{
                var resource_html = "";
                var that = this;
                this.collection.sort();
                _.each(this.collection.models, function (item) {
                    if(item.get('section') == name){
                        resource_html = resource_html + $(that.renderResource(item)).html();
                    }
                }, this);
                if(resource_html.length == 0){
                    resource_html = $(this.no_section_resources_template).html();
                }
                resource_container.html(resource_html);
                this.rebind_resource_buttons();
            }
            return false;
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
            $(this.view_a_resource_modal).on('shown.bs.modal', function (e) {
                $(document).off('focusin.bs.modal');
                e.stopPropagation();
            });
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
            $(this.view_a_resource_modal).on('shown.bs.modal', function (e) {
                $(document).off('focusin.bs.modal');
                e.stopPropagation();
            });
            $(this.view_a_resource_modal).modal('show');
            var that = this;
            $(this.view_a_resource_modal).on('hidden.bs.modal', function () {
                that.refresh();
            });
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
        update_order: function(event){
            var that = this;
            var resource_id;
            $('.section').each(function(){
                var section_name = $(this).data('name');
                var counter = 0;
                $('.resource', this).each(function(){
                    resource_id = $(this).data('resource-id');
                    if(resource_id == undefined){
                        $(this).remove();
                    } else{
                        that.collection.get(resource_id).set({'section': section_name, 'priority': counter});
                        counter = counter + 1;
                    }
                });
            });
            $('.unorganized-resources').each(function(){
                var counter = 0;
                $('.resource', this).each(function(){
                    resource_id = $(this).data('resource-id');
                    that.collection.get(resource_id).set({'section': null, 'priority': counter});
                    counter = counter + 1;
                });
            });
            this.collection.updateAll();
        },
        render: function () {
            var resource_html = "";
            var section_html = "";
            var that = this;
            if(this.section_collection.length > 0){
                _.each(this.section_collection.models, function (item) {
                    section_html = section_html + $(that.renderSection(item)).html();
                }, this);
            } else {
                section_html = $(this.no_sections_template).html();
            }
            if(this.collection.length > 0){
                _.each(this.collection.models, function (item) {
                    if(item.get('section') == undefined){
                        resource_html = resource_html + $(that.renderResource(item)).html();
                    }
                }, this);
            } else {
                resource_html = $(this.no_resources_template).html();
            }
            var tmpl = _.template($(this.template_name).html());
            var content_html = tmpl({
                sections: section_html,
                resources: resource_html,
                classgroup: this.classgroup
            });
            $(this.el).html(content_html);
            this.rebind_events();
            $(this.show_section_resources_link).each(function(){
                this.click();
            });
        },
        renderSection: function(item){
            var sectionView = new this.section_view_class({
                model: item
            });
            return sectionView.render().el;
        },
        renderResource: function (item) {
            var resourceView = new this.view_class({
                model: item
            });
            return resourceView.render().el;
        }
    });

    window.ResourceView = ResourceView;
    window.ResourcesView = ResourcesView;
});