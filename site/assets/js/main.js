/* Hearthside Kitchen — small enhancements. Every page still works without JavaScript. */
(function () {
  "use strict";
  var root = document.documentElement;

  function store(key, val) {
    try {
      if (val === undefined) return localStorage.getItem(key);
      localStorage.setItem(key, val);
    } catch (e) { return null; }
  }

  var toastEl;
  function toast(msg) {
    if (!toastEl) {
      toastEl = document.createElement("div");
      toastEl.className = "toast";
      toastEl.setAttribute("role", "status");
      document.body.appendChild(toastEl);
    }
    toastEl.textContent = msg;
    toastEl.classList.add("show");
    clearTimeout(toast._t);
    toast._t = setTimeout(function () { toastEl.classList.remove("show"); }, 2200);
  }

  // ---- Text size ----
  var sizes = ["", "text-lg", "text-xl"], labels = ["Normal", "Large", "Extra large"];
  function sizeIndex() { for (var i = 1; i < sizes.length; i++) if (root.classList.contains(sizes[i])) return i; return 0; }
  var sizeBtn = document.querySelector(".text-size-btn");
  if (sizeBtn) {
    sizeBtn.addEventListener("click", function () {
      var i = (sizeIndex() + 1) % sizes.length;
      sizes.forEach(function (c) { if (c) root.classList.remove(c); });
      if (sizes[i]) root.classList.add(sizes[i]);
      store("hk-text-size", String(i));
      toast("Text size: " + labels[i]);
    });
  }

  // ---- Servings scaler ----
  var FRACS = [[0, ""], [1 / 8, "1/8"], [1 / 4, "1/4"], [1 / 3, "1/3"], [3 / 8, "3/8"], [1 / 2, "1/2"],
               [5 / 8, "5/8"], [2 / 3, "2/3"], [3 / 4, "3/4"], [7 / 8, "7/8"], [1, ""]];
  function fmt(x) {
    if (x >= 10) return String(Math.round(x));
    var whole = Math.floor(x), frac = x - whole, best = FRACS[0];
    FRACS.forEach(function (f) { if (Math.abs(f[0] - frac) < Math.abs(best[0] - frac)) best = f; });
    if (best[0] === 1) { whole += 1; best = FRACS[0]; }
    if (!whole && !best[1]) return "1/8";
    return whole ? whole + (best[1] ? " " + best[1] : "") : best[1];
  }
  var scaler = document.querySelector("[data-scaler]");
  if (scaler) {
    var qtys = document.querySelectorAll(".qty[data-qty]");
    var servOut = document.getElementById("servings-count");
    var base = parseFloat(servOut.getAttribute("data-base"));
    scaler.addEventListener("click", function (ev) {
      var b = ev.target.closest("button[data-scale]");
      if (!b) return;
      var s = parseFloat(b.getAttribute("data-scale"));
      scaler.querySelectorAll("button").forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
      qtys.forEach(function (q) { q.textContent = fmt(parseFloat(q.getAttribute("data-qty")) * s); });
      servOut.textContent = fmt(base * s);
    });
  }

  // ---- Cook mode: keep the iPhone screen awake (Safari on iOS 16.4+) ----
  var cook = document.getElementById("cook-mode");
  if (cook) {
    var wrap = cook.closest(".cook-mode");
    if (!("wakeLock" in navigator)) {
      wrap.style.display = "none";
    } else {
      var lock = null;
      var request = function () {
        navigator.wakeLock.request("screen").then(function (l) {
          lock = l;
          lock.addEventListener("release", function () { lock = null; });
        }).catch(function () {
          cook.checked = false;
          toast("Cook mode isn't available on this device");
        });
      };
      cook.addEventListener("change", function () {
        if (cook.checked) { request(); toast("Cook mode on: your screen will stay awake"); }
        else if (lock) { lock.release(); toast("Cook mode off"); }
      });
      document.addEventListener("visibilitychange", function () {
        if (document.visibilityState === "visible" && cook.checked && !lock) request();
      });
    }
  }

  // ---- Remember checked ingredients for this recipe during the visit ----
  var ingList = document.querySelector(".ingredients[data-key]");
  if (ingList) {
    var key = "hk-ing-" + ingList.getAttribute("data-key");
    var saved = {};
    try { saved = JSON.parse(sessionStorage.getItem(key) || "{}"); } catch (e) { saved = {}; }
    ingList.querySelectorAll("input[type=checkbox]").forEach(function (box) {
      if (saved[box.id]) box.checked = true;
      box.addEventListener("change", function () {
        saved[box.id] = box.checked;
        try { sessionStorage.setItem(key, JSON.stringify(saved)); } catch (e) { /* ignore */ }
      });
    });
  }

  // ---- Share (opens the iPhone share sheet: Messages, Mail, Facebook...) ----
  document.addEventListener("click", function (ev) {
    var shareBtn = ev.target.closest("[data-share]");
    if (shareBtn) {
      var data = { title: document.title, text: shareBtn.getAttribute("data-share"), url: location.href.split("#")[0] };
      if (navigator.share) {
        navigator.share(data).catch(function () { /* user closed the sheet */ });
      } else if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(data.url).then(function () { toast("Link copied"); });
      } else {
        window.prompt("Copy this link:", data.url);
      }
      return;
    }
    var printBtn = ev.target.closest("[data-print]");
    if (printBtn) { window.print(); }
  });

  // ---- Recipe search (recipes index) ----
  var search = document.getElementById("recipe-search");
  if (search) {
    var cards = Array.prototype.slice.call(document.querySelectorAll("[data-search]"));
    var empty = document.getElementById("no-results");
    var sections = document.querySelectorAll("[data-cat-section]");
    search.addEventListener("input", function () {
      var q = search.value.trim().toLowerCase(), shown = 0;
      cards.forEach(function (c) {
        var hit = !q || c.getAttribute("data-search").indexOf(q) !== -1;
        c.hidden = !hit;
        if (hit) shown++;
      });
      sections.forEach(function (s) { s.hidden = !s.querySelector("[data-search]:not([hidden])"); });
      if (empty) empty.hidden = shown !== 0;
    });
  }

  var y = document.getElementById("year");
  if (y) y.textContent = String(new Date().getFullYear());
})();
