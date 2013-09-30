$(document).ready(function() {
    var option_number = 2;
    var option_template = _.template($("#multipleChoiceOptionTemplate").html());
    $('#add-option-button').click(function() {
        var text_inputs = $('td input[type="text"]');
        var option_numbers = [];
        for(var i=0;i<text_inputs.length;i++){
            option_numbers.push($(text_inputs[i]).data('option-number'))
        }
        option_number = Math.max.apply(Math, option_numbers) + 1;
        var option_html = option_template({
            option_name: "option" + option_number.toString(),
            option_number: option_number
        });
        $('.multiple-choice-creation tbody').append(option_html);
    });
    $('#remove-option-button').click(function() {
        var table_rows = $('.multiple-choice-creation tbody tr');
        $(table_rows).last().remove();
    });
});