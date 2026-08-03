(function () {
  "use strict";

  var timeEl = document.getElementById("clock-time");
  var dateEl = document.getElementById("clock-date");

  var WEEKDAYS = ["воскресенье", "понедельник", "вторник", "среда", "четверг", "пятница", "суббота"];
  var MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"];

  function pad(n) { return String(n).padStart(2, "0"); }

  function tickClock() {
    var now = new Date();
    timeEl.textContent = pad(now.getHours()) + ":" + pad(now.getMinutes()) + ":" + pad(now.getSeconds());
    dateEl.textContent = WEEKDAYS[now.getDay()] + ", " + now.getDate() + " " + MONTHS[now.getMonth()];
  }

  if (timeEl) {
    tickClock();
    setInterval(tickClock, 1000);
  }

  // ---------- Секундомер ----------
  var swTimeEl = document.getElementById("sw-time");
  var btnStart = document.getElementById("sw-start");
  var btnLap = document.getElementById("sw-lap");
  var btnReset = document.getElementById("sw-reset");
  var lapList = document.getElementById("lap-list");

  if (!swTimeEl) return;

  var startTs = 0;
  var elapsed = 0;
  var running = false;
  var rafId = null;
  var lapCount = 0;

  function formatMs(ms) {
    var totalCs = Math.floor(ms / 10);
    var cs = totalCs % 100;
    var totalSec = Math.floor(totalCs / 100);
    var s = totalSec % 60;
    var m = Math.floor(totalSec / 60);
    return pad(m) + ":" + pad(s) + "." + pad(cs);
  }

  function renderSw() {
    var current = elapsed + (running ? Date.now() - startTs : 0);
    swTimeEl.textContent = formatMs(current);
  }

  function loop() {
    renderSw();
    if (running) rafId = requestAnimationFrame(loop);
  }

  btnStart.addEventListener("click", function () {
    if (running) {
      running = false;
      elapsed += Date.now() - startTs;
      btnStart.textContent = "▶";
      cancelAnimationFrame(rafId);
    } else {
      running = true;
      startTs = Date.now();
      btnStart.textContent = "❚❚";
      loop();
    }
  });

  btnLap.addEventListener("click", function () {
    if (!running && elapsed === 0) return;
    lapCount += 1;
    var current = elapsed + (running ? Date.now() - startTs : 0);
    var li = document.createElement("li");
    li.className = "glass-row";
    li.innerHTML = '<span>Круг ' + lapCount + '</span><span>' + formatMs(current) + '</span>';
    lapList.prepend(li);
  });

  btnReset.addEventListener("click", function () {
    running = false;
    elapsed = 0;
    lapCount = 0;
    cancelAnimationFrame(rafId);
    btnStart.textContent = "▶";
    lapList.innerHTML = "";
    renderSw();
  });

  renderSw();
})();
