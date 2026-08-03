(function () {
  "use strict";

  // Карточка запроса разрешения на уведомления (только на этой странице).
  // Периодическая проверка напоминаний подключена глобально в base.html
  // через notify-check.js — так уведомления приходят на любой странице.
  var permCard = document.getElementById("notif-permission-card");
  var btnEnable = document.getElementById("btn-enable-notif");

  if (window.Notification && permCard) {
    if (Notification.permission === "default") {
      permCard.style.display = "block";
    }
    if (btnEnable) {
      btnEnable.addEventListener("click", function () {
        Notification.requestPermission().then(function () {
          permCard.style.display = "none";
        });
      });
    }
  }
})();
