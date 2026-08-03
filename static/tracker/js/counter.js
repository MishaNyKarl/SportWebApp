(function () {
  "use strict";

  var valueEl = document.getElementById("reps-value");
  var hidden = document.getElementById("reps-hidden");
  var btnInc = document.getElementById("btn-inc");
  var btnDec = document.getElementById("btn-dec");
  var form = document.getElementById("set-form");

  if (!valueEl || !hidden) return;

  var reps = 0;

  function render() {
    valueEl.textContent = String(reps);
    hidden.value = String(reps);
  }

  function vibrate() {
    if (navigator.vibrate) navigator.vibrate(15);
  }

  btnInc.addEventListener("click", function () {
    reps += 1;
    render();
    vibrate();
  });

  btnDec.addEventListener("click", function () {
    reps = Math.max(0, reps - 1);
    render();
    vibrate();
  });

  if (form) {
    form.addEventListener("submit", function () {
      hidden.value = String(reps);
    });
  }

  render();

  // --- Недавние упражнения: клик по чипу выбирает его в select ---
  var exerciseSelect = document.getElementById("id_exercise");
  var recentChips = document.getElementById("recent-exercise-chips");
  if (recentChips && exerciseSelect) {
    recentChips.addEventListener("click", function (e) {
      var chip = e.target.closest(".chip");
      if (!chip) return;
      exerciseSelect.value = chip.dataset.exerciseId;
      Array.prototype.forEach.call(recentChips.querySelectorAll(".chip"), function (c) {
        c.classList.remove("active");
      });
      chip.classList.add("active");
    });
  }

  // --- Модалка добавления упражнения (шестерёнка) ---
  var modalOverlay = document.getElementById("exercise-modal-overlay");
  var btnOpenModal = document.getElementById("btn-open-exercise-modal");
  var btnCloseModal = document.getElementById("btn-close-exercise-modal");
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
})();
