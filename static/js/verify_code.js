$(document).ready(function() {
    var message_class = '#verify-code-message';
    var verify_code_form = '.verify-code-form';
    var verify_code_button = '#verify-code';

    var error_display = function(model, xhr, options){
        $(verify_code_form).removeClass("has-success").addClass("has-error");
        $(message_class).html("Incorrect code.  Please try again or contact the course owner.");
        $(verify_code_button).attr('disabled', false);
    };
    var success_display = function(model, response, options){
        location.reload();
    };
    $(verify_code_button).click( function(event){
        event.preventDefault();
        $(event.target).attr('disabled', true);
        var code = $("#inputClass1").val();
        var class_name = $("#class-name").data('class-name');
        var post_data = {
            code: code,
            class_name: class_name
        }
        window.post_code(post_data, success_display, error_display);
        return false;
    });
});
