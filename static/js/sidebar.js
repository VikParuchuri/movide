$(document).ready(function() {
    var classview = new window.ClassesSidebarView();
    classview.render_sidebar();
    $('[data-toggle=offcanvas]').click(function() {
        $('.row-offcanvas').toggleClass('active');
    });
});
