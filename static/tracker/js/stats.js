(function () {
  "use strict";

  if (!window.Chart || !window.STATS_DATA) return;

  var data = window.STATS_DATA;
  var isDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  var gridColor = isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.06)";
  var textColor = isDark ? "rgba(245,246,248,0.65)" : "rgba(20,22,30,0.55)";

  Chart.defaults.font.family = "-apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif";
  Chart.defaults.color = textColor;

  var dailyCtx = document.getElementById("chart-daily");
  if (dailyCtx) {
    new Chart(dailyCtx, {
      type: "bar",
      data: {
        labels: data.dailyLabels,
        datasets: [{
          label: "Повторения",
          data: data.dailyReps,
          backgroundColor: "rgba(10, 132, 255, 0.55)",
          borderRadius: 6,
          maxBarThickness: 18,
        }],
      },
      options: {
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false } },
          y: { beginAtZero: true, grid: { color: gridColor } },
        },
      },
    });
  }

  var weeklyCtx = document.getElementById("chart-weekly");
  if (weeklyCtx) {
    new Chart(weeklyCtx, {
      type: "line",
      data: {
        labels: data.weeklyLabels,
        datasets: [{
          label: "Тоннаж, кг",
          data: data.weeklyVolume,
          borderColor: "#30D158",
          backgroundColor: "rgba(48, 209, 88, 0.18)",
          fill: true,
          tension: 0.35,
          pointRadius: 3,
        }],
      },
      options: {
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false } },
          y: { beginAtZero: true, grid: { color: gridColor } },
        },
      },
    });
  }

  // --- Модалка "тренировка из прошлого" ---
  var modalOverlay = document.getElementById("past-modal-overlay");
  var btnOpenModal = document.getElementById("btn-open-past-modal");
  var btnCloseModal = document.getElementById("btn-close-past-modal");
  if (modalOverlay && btnOpenModal) {
    btnOpenModal.addEventListener("click", function () {
      modalOverlay.classList.add("open");
    });
  }
  if (modalOverlay && btnCloseModal) {
    btnCloseModal.addEventListener("click", function () {
      modalOverlay.classList.remove("open");
    });
  }
  if (modalOverlay) {
    modalOverlay.addEventListener("click", function (e) {
      if (e.target === modalOverlay) modalOverlay.classList.remove("open");
    });
  }

  // --- Импорт тренировки из JSON ---
  var btnImport = document.getElementById("btn-json-import");
  var importInput = document.getElementById("json-import-input");
  var importResult = document.getElementById("json-import-result");
  if (btnImport && importInput && window.IMPORT_URL) {
    btnImport.addEventListener("click", function () {
      var payload;
      try {
        payload = JSON.parse(importInput.value);
      } catch (e) {
        importResult.textContent = "Ошибка: некорректный JSON";
        return;
      }
      importResult.textContent = "Импортируем...";
      fetch(window.IMPORT_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
        .then(function (res) { return res.json().then(function (data) { return { status: res.status, data: data }; }); })
        .then(function (result) {
          if (result.data.ok) {
            importResult.textContent = "Готово: добавлено подходов — " + result.data.created_entries +
              (result.data.errors.length ? "; ошибки: " + result.data.errors.join(", ") : "");
            setTimeout(function () { window.location.reload(); }, 1200);
          } else {
            importResult.textContent = "Ошибка: " + (result.data.error || "неизвестная");
          }
        })
        .catch(function () {
          importResult.textContent = "Ошибка сети";
        });
    });
  }
})();
