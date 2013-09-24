$(document).ready(function() {
    var classview = new window.ClassesView();
    classview.render_dash();

    var message_class = '#create-class-message';
    var create_class_form = '.create-class-form';
    var create_class_button = '#create-class';

    var error_display = function(model, xhr, options){
        $(create_class_form).removeClass("has-success").addClass("has-error");
        $(message_class).html("This class name has been taken.  Please try another.");
        $(create_class_button).attr('disabled', false);
    };
    var success_display = function(model, response, options){
        $(create_class_form).removeClass("has-error").addClass("has-success");
        $(message_class).html("Class created!  Click on the class name below to get started.  You may need to reload the page to see it.");
        $("#refresh-sidebar").click();
        classview.refresh();
        $(create_class_button).attr('disabled', false);
    };
    $(create_class_button).click( function(event){
        event.preventDefault();
        $(event.target).attr('disabled', true);
        var class_name = $("#inputClass1").val();
        var classgroup = new Class({'name' : class_name});
        classgroup.save(null,{success : success_display, error: error_display, async: false});
        return false;
    });
});