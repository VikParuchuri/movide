$(document).ready(function() {
    var message_class = '#status-message';
    var verify_code_form = '.submit-form';
    var verify_code_button = '#verify-code';

    var error_display = function(model, xhr, options){
        $(verify_code_form).removeClass("has-success").addClass("has-error");
        $(message_class).html(model.responseText);
        $(verify_code_button).attr('disabled', false);
    };
    var success_display = function(model, response, options){
        $(verify_code_button).attr('disabled', false);
        location.reload();
    };
    $(verify_code_button).click( function(event){
        event.preventDefault();
        $(event.target).attr('disabled', true);
        var username = $("#username").val();
        var password = $("#password").val();
        var class_name = $("#class-name").data('class-name');
        var post_data = {
            class_name: class_name,
            username: username,
            password: password
        };
        window.csrf_post("/signup_and_class_code/", post_data, success_display, error_display);
        return false;
    });
});
