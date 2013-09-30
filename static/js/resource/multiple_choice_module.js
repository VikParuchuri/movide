$(document).ready(function() {
    var resource_id = $('.resource-container').data('resource-id');
    $('#multiple-choice-submit').click(function() {
        var selected = $(".multiple-choice-options input[type='radio']:checked");
        var selected_value;
        if(selected.length > 0){
            selected_value = selected.val();
            window.csrf_post(
                "/api/resources/" + resource_id.toString() + "/",
                {'action': 'save_answer', answer: selected_value},
                function(response){
                    var correct = JSON.parse(response).correct;
                    if(correct == true){
                        $(".resource-container .help-block").html("You got the answer right!")
                    } else {
                        $(".resource-container .help-block").html("Incorrect response.")
                    }
                }
            )
        } else {
            $(".resource-container .help-block").html("Please select an option.")
        }
    });
});
