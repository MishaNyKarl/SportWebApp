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
})();
