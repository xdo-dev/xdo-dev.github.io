(function () {
  "use strict";

  /* theme toggle */
  var toggle = document.getElementById("themeToggle");
  if (toggle) {
    toggle.addEventListener("click", function () {
      var root = document.documentElement;
      var next =
        root.getAttribute("data-theme") === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try {
        localStorage.setItem("xdo-theme", next);
      } catch (e) {
        /* private browsing: preference not saved */
      }
    });
  }

  /* mobile navigation */
  var navToggle = document.getElementById("navToggle");
  var header = document.querySelector(".site-header");
  if (navToggle && header) {
    navToggle.addEventListener("click", function () {
      var open = header.classList.toggle("nav-open");
      navToggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }
})();
