(function() {
  $(function() {
    $(".animated-when-visible").each(function(i, el) {
      el = $(el);
      if (el.visible(true)) {
        return el.addClass("animated " + el.data("animation-type"));
      }
    });
    $(window).scroll(function(event) {
      return $(".animated-when-visible").each(function(i, el) {
        el = $(el);
        if (el.visible(true)) {
          return el.addClass("animated " + el.data("animation-type"));
        }
      });
    });
    $(".dial").knob({
      readOnly: true,
      draw: function() {
        return $(this.i).val(this.cv + "%");
      }
    });
    $.scrollUp({
      scrollText: "<i class='icon-chevron-up'></i>"
    });
    $(".isotope-w").isotope({
      itemSelector: '.item',
      layoutMode: 'fitRows'
    });
    return $(".portfolio-filters a").click(function() {
      var selector;
      selector = $(this).attr("data-filter");
      $(".isotope-w").isotope({
        filter: selector
      });
      return false;
    });
  });

}).call(this);
