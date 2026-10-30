/* Peaker — site script: mobile menu and contact form. No dependencies. */
(function () {
  "use strict";

  // Mobile menu
  var btn = document.querySelector(".menu-btn");
  var panel = document.getElementById("nav-panel");
  if (btn && panel) {
    var label = btn.querySelector(".sr-only");
    var setOpen = function (open) {
      panel.classList.toggle("open", open);
      btn.setAttribute("aria-expanded", open ? "true" : "false");
      if (label) label.textContent = open ? btn.dataset.close : btn.dataset.open;
    };
    btn.addEventListener("click", function () { setOpen(btn.getAttribute("aria-expanded") !== "true"); });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && btn.getAttribute("aria-expanded") === "true") { setOpen(false); btn.focus(); }
    });
  }

  // Contact form: posts JSON to /api/lead, which creates a lead in Odoo CRM.
  var form = document.getElementById("lead-form");
  if (!form) return;
  var status = document.getElementById("form-status");
  var submit = form.querySelector("button[type=submit]");
  var submitText = submit.textContent;

  var show = function (kind, text) {
    status.className = "status " + kind;
    status.textContent = text;
  };

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var required = ["name", "email", "message"];
    var firstBad = null;
    required.forEach(function (id) {
      var el = form.elements[id];
      var bad = !el.value.trim() || (id === "email" && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(el.value.trim()));
      el.setAttribute("aria-invalid", bad ? "true" : "false");
      if (bad && !firstBad) firstBad = el;
    });
    if (firstBad) { show("err", form.dataset.invalid); firstBad.focus(); return; }

    var data = {};
    new FormData(form).forEach(function (v, k) { data[k] = String(v).trim(); });
    data.page = location.pathname;

    submit.disabled = true;
    submit.textContent = form.dataset.sending;
    status.className = "status";

    fetch(form.action, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function () {
        form.reset();
        show("ok", form.dataset.success);
      })
      .catch(function () { show("err", form.dataset.error); })
      .finally(function () { submit.disabled = false; submit.textContent = submitText; });
  });
})();
