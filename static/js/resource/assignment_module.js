window.AssignmentUser = (function(el) {
    var resource_id = $(el).data('resource-id');

    var submit_answer = (function(event){
        event.preventDefault();
        var action = $(event.target).data('action');
        var answer_input = $('.answer-input', el);
        var answer = " ";
        if(answer_input.length > 0){
            answer = answer_input.val();
        }
        if(answer.length > 0 || action == "try_again"){
            window.csrf_post(
                "/api/resources/" + resource_id.toString() + "/",
                {'action': action, answer: answer},
                function(response){
                    var html = response.html;
                    $(".help-block", el).html(response.message);
                    if(response.html != null){
                        $(el).html(html);
                        rebind_events();
                    }
                }
            )
        }
        else {
            $(".help-block", el).html("Please enter an answer.")
        }
    });

    var setup_editor = function() {
        var answer = $('.answer-input', el);
        if(answer.length > 0){
            var editor_options = JSON.parse($('.editor-options', el).html());
            $(answer).redactor(editor_options);
        }
    };

    var rebind_events = function() {
        $('.submit', el).click(submit_answer);
        setup_editor();
    };

    rebind_events();
});
