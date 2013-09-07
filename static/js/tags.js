$(document).ready(function() {
    var tagview = new window.TagsView();
    tagview.render_dash();

    var error_display = function(model, xhr, options){
        $(".create-tag-form").removeClass("has-success").addClass("has-error");
        $(".help-block").html("This tag has been taken.  Please try another.");
    };
    var success_display = function(model, response, options){
        $(".create-tag-form").removeClass("has-error").addClass("has-success");
        $(".help-block").html("Tag created!  Click the tag on the left to add students.");
        $("#refresh-sidebar").click();
        tagview.refresh();
    };
    $("#create-tag").click( function(event){
        event.preventDefault();
        var tag_name = $("#inputTag1").val();
        if(tag_name.charAt(0)!="#"){
            tag_name = "#" + tag_name;
        }
        var tag = new Tag({'name' : tag_name});
        tag.save(null,{success : success_display, error: error_display});
        return false;
    })
});