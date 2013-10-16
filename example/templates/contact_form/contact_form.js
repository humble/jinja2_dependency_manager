(function () {
  "use strict";

  $(document).ready(function() {
    $("#close-contact-form").click(function(e) {
      e.preventDefault();
      $(".contact-form").fadeOut();
    });
    $('#contact-submit').click(function(e) {
      e.preventDefault();
      $(".contact-form form").animate({"opacity": 0});
      $("#confirmation").fadeIn()
      $(".contact-form").delay(2000).fadeOut();
    });
  });

  function showContactForm(e) {
    e.preventDefault();
    $(".contact-form form").css({"opacity": 1});
    $("#confirmation").hide()
    $(".contact-form").fadeIn();
  }

  window.showContactForm = showContactForm;
})();
