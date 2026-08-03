(function () {
  "use strict";

  var RADIUS = 110;
  var CIRCUMFERENCE = 2 * Math.PI * RADIUS;

  var ring = document.getElementById("ring-progress");
  var display = document.getElementById("timer-display");
  var statusEl = document.getElementById("timer-status");
  var btnStart = document.getElementById("btn-start");
  var btnReset = document.getElementById("btn-reset");
  var btnPlus10 = document.getElementById("btn-plus10");
  var btnMinus10 = document.getElementById("btn-minus10");
  var presets = document.getElementById("presets");

  if (!ring || !display) return;

  ring.style.strokeDasharray = CIRCUMFERENCE.toFixed(2);
  ring.style.strokeDashoffset = "0";

  var totalSeconds = 60;
  var remaining = totalSeconds;
  var running = false;
  var intervalId = null;

  function formatTime(sec) {
    sec = Math.max(0, Math.round(sec));
    var m = Math.floor(sec / 60);
    var s = sec % 60;
    return String(m).padStart(2, "0") + ":" + String(s).padStart(2, "0");
  }

  function updateDisplay() {
    display.textContent = formatTime(remaining);
    var fraction = totalSeconds > 0 ? remaining / totalSeconds : 0;
    var offset = CIRCUMFERENCE * (1 - fraction);
    ring.style.strokeDashoffset = offset.toFixed(2);
    ring.style.stroke = remaining <= 5 && remaining > 0 ? "var(--accent-red)" : "var(--accent-blue)";
  }

  function setStatus(text) {
    statusEl.textContent = text;
  }

  function beep() {
    try {
      var ctx = new (window.AudioContext || window.webkitAudioContext)();
      var osc = ctx.createOscillator();
      var gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.value = 880;
      gain.gain.setValueAtTime(0.001, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.3, ctx.currentTime + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
      osc.connect(gain).connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.55);
    } catch (e) { /* audio недоступно — молча пропускаем */ }
  }

  function notifyDone() {
    beep();
    if (navigator.vibrate) navigator.vibrate([200, 100, 200]);
    if (window.Notification && Notification.permission === "granted") {
      new Notification("Отдых окончен", { body: "Пора приступать к следующему подходу" });
    }
    addHistoryEntry(totalSeconds);
  }

  // --- История таймеров (хранится в localStorage браузера) ---
  var HISTORY_KEY = "sportapp_timer_history";
  var HISTORY_LIMIT = 20;
  var historyList = document.getElementById("timer-history");
  var btnClearHistory = document.getElementById("btn-clear-history");

  function loadHistory() {
    try {
      return JSON.parse(localStorage.getItem(HISTORY_KEY)) || [];
    } catch (e) {
      return [];
    }
  }

  function saveHistory(items) {
    try {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(items));
    } catch (e) { /* localStorage недоступен — молча пропускаем */ }
  }

  function renderHistory() {
    if (!historyList) return;
    var items = loadHistory();
    historyList.innerHTML = "";
    if (!items.length) {
      historyList.innerHTML = '<li class="history-empty">Пока нет завершённых отдыхов</li>';
      return;
    }
    items.forEach(function (item) {
      var li = document.createElement("li");
      li.className = "history-row";
      li.innerHTML = '<span class="history-time">' + item.time + '</span>' +
        '<span class="history-sec">' + formatTime(item.seconds) + '</span>';
      historyList.appendChild(li);
    });
  }

  function addHistoryEntry(seconds) {
    var items = loadHistory();
    var now = new Date();
    var hh = String(now.getHours()).padStart(2, "0");
    var mm = String(now.getMinutes()).padStart(2, "0");
    items.unshift({ time: hh + ":" + mm, seconds: seconds });
    items = items.slice(0, HISTORY_LIMIT);
    saveHistory(items);
    renderHistory();
  }

  if (btnClearHistory) {
    btnClearHistory.addEventListener("click", function () {
      saveHistory([]);
      renderHistory();
    });
  }

  function tick() {
    remaining -= 1;
    if (remaining <= 0) {
      remaining = 0;
      updateDisplay();
      stop();
      setStatus("Готово!");
      notifyDone();
      return;
    }
    updateDisplay();
  }

  function start() {
    if (running) return;
    running = true;
    btnStart.textContent = "❚❚";
    setStatus("Отдых...");
    intervalId = setInterval(tick, 1000);
  }

  function pause() {
    running = false;
    btnStart.textContent = "▶";
    setStatus("Пауза");
    clearInterval(intervalId);
  }

  function stop() {
    running = false;
    btnStart.textContent = "▶";
    clearInterval(intervalId);
  }

  function reset() {
    stop();
    remaining = totalSeconds;
    setStatus("Готов");
    updateDisplay();
  }

  btnStart.addEventListener("click", function () {
    if (running) pause(); else start();
  });

  btnReset.addEventListener("click", reset);

  btnPlus10.addEventListener("click", function () {
    totalSeconds += 10;
    remaining += 10;
    updateDisplay();
  });

  btnMinus10.addEventListener("click", function () {
    totalSeconds = Math.max(10, totalSeconds - 10);
    remaining = Math.max(0, Math.min(remaining, totalSeconds));
    updateDisplay();
  });

  if (presets) {
    presets.addEventListener("click", function (e) {
      var chip = e.target.closest(".chip");
      if (!chip) return;
      Array.prototype.forEach.call(presets.querySelectorAll(".chip"), function (c) {
        c.classList.remove("active");
      });
      chip.classList.add("active");
      var sec = parseInt(chip.dataset.sec, 10);
      totalSeconds = sec;
      remaining = sec;
      stop();
      setStatus("Готов");
      updateDisplay();
    });
  }

  if (window.Notification && Notification.permission === "default") {
    // Тихо не запрашиваем на этой странице — попросим на странице напоминаний.
  }

  updateDisplay();
  renderHistory();
})();
