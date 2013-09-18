$(document).ready(function() {
    var info_id = "#classinfo";
    var options = {
        classgroup: $(info_id).data('name'),
        display_tag:$(info_id).data('display-name')
    };
    var detail_view = new ClassDetailView(options);
    detail_view.render();
    $('[data-toggle=offcanvas]').click(function() {
        $('.row-offcanvas').toggleClass('active');
    });
});