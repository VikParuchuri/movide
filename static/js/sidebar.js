$(document).ready(function() {
    var tagview = new window.TagsSidebarView();
    tagview.render_sidebar();
    $('[data-toggle=offcanvas]').click(function() {
        $('.row-offcanvas').toggleClass('active');
    });
});
