$(document).ready(function() {
    var tagview = new window.TagsView();
    tagview.render_dash();

    var message_tag = '#create-tag-message';
    var create_tag_form = '.create-tag-form';
    var create_tag_button = '#create-tag';

    var error_display = function(model, xhr, options){
        $(create_tag_form).removeClass("has-success").addClass("has-error");
        $(message_tag).html("This tag has been taken.  Please try another.");
        $(create_tag_button).attr('disabled', false);
    };
    var success_display = function(model, response, options){
        $(create_tag_form).removeClass("has-error").addClass("has-success");
        $(message_tag).html("Tag created!  Click the tag on the left to add students.");
        $("#refresh-sidebar").click();
        tagview.refresh();
        $(create_tag_button).attr('disabled', false);
    };
    $(create_tag_button).click( function(event){
        event.preventDefault();
        $(event.target).attr('disabled', true);
        var tag_name = $("#inputTag1").val();
        if(tag_name.charAt(0)!="#"){
            tag_name = "#" + tag_name;
        }
        var tag = new Tag({'name' : tag_name});
        tag.save(null,{success : success_display, error: error_display});
        return false;
    });
});