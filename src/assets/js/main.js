/* Peaker site script: header, menu, hero motion, reveals, counters, game, contact form. No dependencies. */
(function () {
  "use strict";
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var rtl = document.documentElement.dir === "rtl";
  var lang = document.documentElement.lang;

  /* ---------- header: solid on scroll, hides when scrolling down ---------- */
  var header = document.querySelector(".site-header");
  var lastY = window.scrollY;
  var ticking = false;
  function onScroll() {
    var y = window.scrollY;
    header.classList.toggle("scrolled", y > 12);
    if (!document.body.classList.contains("menu-open")) {
      header.classList.toggle("hidden", y > 500 && y > lastY + 4);
      if (y < lastY - 4) header.classList.remove("hidden");
    }
    lastY = y; ticking = false;
  }
  window.addEventListener("scroll", function () { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } }, { passive: true });
  onScroll();

  /* ---------- mobile menu ---------- */
  var btn = document.querySelector(".menu-btn");
  var panel = document.getElementById("nav-panel");
  if (btn && panel) {
    var label = btn.querySelector(".sr-only");
    var setOpen = function (open) {
      panel.classList.toggle("open", open);
      document.body.classList.toggle("menu-open", open);
      btn.setAttribute("aria-expanded", open ? "true" : "false");
      if (label) label.textContent = open ? btn.dataset.close : btn.dataset.open;
    };
    btn.addEventListener("click", function () { setOpen(btn.getAttribute("aria-expanded") !== "true"); });
    panel.addEventListener("click", function (e) { if (e.target.closest("a")) setOpen(false); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape" && panel.classList.contains("open")) { setOpen(false); btn.focus(); } });
  }

  /* ---------- hero: rotating words ---------- */
  var rot = document.querySelector(".rotator");
  if (rot && !reduce) {
    var words = rot.querySelectorAll("span"), i = 0;
    setInterval(function () {
      if (document.hidden) return;
      var cur = words[i]; i = (i + 1) % words.length; var nxt = words[i];
      cur.classList.remove("on"); cur.classList.add("out");
      nxt.classList.remove("out"); nxt.classList.add("on");
      setTimeout(function () { cur.classList.remove("out"); }, 650);
    }, 2400);
  }

  /* ---------- hero: parallax collage ---------- */
  var collage = document.querySelector(".collage");
  if (collage && !reduce && window.matchMedia("(pointer: fine)").matches) {
    var layers = collage.querySelectorAll("[data-depth]");
    var hero = collage.closest(".hero");
    var tx = 0, ty = 0, raf = 0;
    hero.addEventListener("pointermove", function (e) {
      var r = hero.getBoundingClientRect();
      tx = (e.clientX - r.left) / r.width - 0.5; ty = (e.clientY - r.top) / r.height - 0.5;
      if (!raf) raf = requestAnimationFrame(function () {
        layers.forEach(function (l) {
          var d = +l.dataset.depth;
          l.style.transform = "translate3d(" + (-tx * d).toFixed(1) + "px," + (-ty * d).toFixed(1) + "px,0)";
        });
        raf = 0;
      });
    });
    hero.addEventListener("pointerleave", function () { layers.forEach(function (l) { l.style.transform = ""; }); });
  }

  /* ---------- count-up numbers ---------- */
  var fmt = new Intl.NumberFormat(lang === "ar" ? "ar-EG" : "en-US");
  function countUp(el) {
    var target = +el.dataset.count, pre = el.dataset.pre || "", suf = el.dataset.suf || "";
    if (reduce) return;
    var t0 = null, dur = 1400;
    function step(t) {
      if (!t0) t0 = t;
      var p = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - p, 3);
      el.textContent = pre + fmt.format(Math.round(target * e)) + suf;
      if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  /* ---------- reveal on scroll ---------- */
  var io = "IntersectionObserver" in window ? new IntersectionObserver(function (entries) {
    entries.forEach(function (en) {
      if (!en.isIntersecting) return;
      var el = en.target;
      el.classList.add("in");
      el.querySelectorAll("[data-count]").forEach(countUp);
      if (el.matches("[data-count]")) countUp(el);
      io.unobserve(el);
    });
  }, { rootMargin: "0px 0px -8% 0px", threshold: 0.12 }) : null;
  document.querySelectorAll("[data-reveal], [data-steps]").forEach(function (el) {
    if (io) io.observe(el); else el.classList.add("in");
  });

  /* ---------- play the game in place ---------- */
  document.querySelectorAll(".game-frame button[data-src]").forEach(function (b) {
    b.addEventListener("click", function () {
      var f = document.createElement("iframe");
      f.src = b.dataset.src; f.title = b.dataset.title || "Game"; f.allow = "fullscreen";
      var box = b.parentNode; box.innerHTML = ""; box.appendChild(f); f.focus();
    });
  });

  /* ---------- services page: highlight the section in view ---------- */
  var toc = document.querySelectorAll(".toc a");
  if (toc.length && io) {
    var map = {};
    toc.forEach(function (a) { map[a.getAttribute("href").slice(1)] = a; });
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { toc.forEach(function (a) { a.classList.remove("active"); }); var a = map[en.target.id]; if (a) a.classList.add("active"); }
      });
    }, { rootMargin: "-40% 0px -55% 0px" });
    document.querySelectorAll(".svc[id]").forEach(function (s) { spy.observe(s); });
  }

  /* ---------- contact form -> /api/lead -> Odoo CRM ---------- */
  var form = document.getElementById("lead-form");
  if (!form) return;
  var status = document.getElementById("form-status");
  var submit = form.querySelector("button[type=submit]");
  var submitHTML = submit.innerHTML;
  var show = function (kind, text) { status.className = "status " + kind; status.textContent = text; };
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var firstBad = null;
    ["name", "email", "message"].forEach(function (id) {
      var el = form.elements[id];
      var bad = !el.value.trim() || (id === "email" && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(el.value.trim()));
      el.setAttribute("aria-invalid", bad ? "true" : "false");
      if (bad && !firstBad) firstBad = el;
    });
    if (firstBad) { show("err", form.dataset.invalid); firstBad.focus(); return; }
    var data = {};
    new FormData(form).forEach(function (v, k) { data[k] = String(v).trim(); });
    data.page = location.pathname;
    submit.disabled = true; submit.textContent = form.dataset.sending; status.className = "status";
    fetch(form.action, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function () { form.reset(); show("ok", form.dataset.success); })
      .catch(function () { show("err", form.dataset.error); })
      .finally(function () { submit.disabled = false; submit.innerHTML = submitHTML; });
  });
})();
