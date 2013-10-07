window.VerticalAuthor= (function(el) {
    var vertical_id = $(el).data('resource-id');
    var create_item = function(event){
        event.preventDefault();
        var resource_type = $(event.target).data('resource-type');
        var author_html = $.getValues("/api/resources/author", {classgroup: $(el).data('class-name'), resource_type: resource_type, vertical_id: vertical_id}).html;
        $(el).find('.child-container').append(author_html);
        rebind();
        return false;
    };

    var rebind_creation = (function() {
        var resource_creation_form = $('.resource-creation-form', el);
        resource_creation_form.unbind();
        resource_creation_form.each(function(){
            var resource_author_container = $(this).closest('.resource-author-container');
            $(this).ajaxForm({
                success: function() {
                    $(resource_author_container).find('.help-block-resource').html('Successfully saved the module.')
                },
                data: {
                    classgroup: resource_author_container.data('class-name'),
                    resource_type: resource_author_container.data('resource-type'),
                    resource_id: resource_author_container.data('resource-id'),
                    vertical_id: $(el).data('resource-id')
                },
                error: function(){
                    $(resource_author_container).find('.help-block-resource').html('Could not save the module.')
                }

            });
        });
    });

    var rebind = function(){
        $('.resource-type-button', el).unbind();
        $('.resource-type-button', el).click(create_item);
        $('.child-container', el).unbind();
        $('.child-container', el).sortable({
            placeholder: "ui-state-highlight",
            helper:'clone',
            axis: 'y',
            delay: 150,
            update: function( event, ui ) {
                update_order();
            }
        });

        $('.child-container .component-removal-button', el).unbind();
        $('.child-container .component-removal-button', el).click(delete_item);

        $('.component-visibility-selection a', el).unbind();
        $('.component-visibility-selection a', el).click(change_visibility);

        rebind_creation();
    };

    var delete_item = function(event){
        var resource_author_container = $(this).closest('.resource-author-container');
        var resource_id = resource_author_container.data('resource-id');
        resource_author_container.remove();
        window.csrf_delete("/api/resources/" + resource_id + "/", {}, null, null);
    };

    var change_visibility = function(event){
        var resource_author_container = $(this).closest('.resource-author-container');
        var resource_id = resource_author_container.data('resource-id');
        var new_role = $(event.target).data('name');
        var new_role_title = $(event.target).html();
        window.csrf_post("/api/resources/" + resource_id + "/",
            {action: 'change_visibility', new_role: new_role},
            function(){
                $('.component-visibility-button .current-role', resource_author_container).html(new_role_title);
            },
            null
        );
    };

    var update_order = function(){
        var child_ids = [];
        $('.child-container .resource-author-container', el).each(function(){
            child_ids.push($(this).data('resource-id'));
        });

        window.csrf_post("/api/resources/" + vertical_id + "/", {action: 'reorder_modules', child_ids: child_ids}, null, null);
    };

    rebind();
});
