$(document).ready(function() {
    var signup_message = "#email-signup-message";
    var signup_button = "#email-signup-button";
    var error_display = function(model, xhr, options){
        $(signup_message).removeClass("has-success").addClass("has-error");
        $(signup_message).html("<p class='text-danger'>Uh oh.  For some reason, we can't sign you up at this time.  Are you sure you aren't already subscribed?</p>");
        $(signup_button).attr('disabled', false);
    };
    var success_display = function(model, response, options){
        $(signup_message).removeClass("has-error").addClass("has-success");
        $(signup_message).html("<p class='text-success'>Thank you for subscribing to the movide newsletter!</p>");
        $(signup_button).attr('disabled', false);
    };
    $(signup_button).click( function(event){
        event.preventDefault();
        $(event.target).attr('disabled', true);
        var email_address = $("#email-signup-address").val();
        var email = new EmailSubscription({email_address : email_address});
        email.save(null,{success : success_display, error: error_display});
        return false;
    });
});