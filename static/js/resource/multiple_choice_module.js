window.MultipleChoiceUser = (function(el) {
    var resource_id = $(el).data('resource-id');
    var submit_answer = (function(){
        var selected = $(".multiple-choice-options input[type='radio']:checked", el);
        var selected_value;
        if(selected.length > 0){
            selected_value = selected.val();
            window.csrf_post(
                "/api/resources/" + resource_id.toString() + "/",
                {'action': 'save_answer', answer: selected_value},
                function(response){
                    response = JSON.parse(response);
                    var html = response.html;
                    $(el).html(html);
                    $('.multiple-choice-submit', el).click(submit_answer);
                }
            )
        } else {
            $(".help-block", el).html("Please select an option.")
        }
    });

    $('.multiple-choice-submit', el).click(submit_answer);
});
