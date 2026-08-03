(function () {
  "use strict";

  // Периодическая проверка напоминаний — работает на любой странице,
  // пока приложение открыто в браузере. Подключено глобально в base.html.
  var DAY_CODES = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"];
  var lastFiredKey = "sportapp_last_fired_reminder";

  function checkReminders() {
    if (!window.Notification || Notification.permission !== "granted") return;

    fetch("/api/reminders/")
      .then(function (r) { return r.json(); })
      .then(function (payload) {
        var now = new Date();
        var hhmm = String(now.getHours()).padStart(2, "0") + ":" + String(now.getMinutes()).padStart(2, "0");
        var today = DAY_CODES[now.getDay()];

        payload.reminders.forEach(function (r) {
          var daysOk = r.days.length === 0 || r.days.indexOf(today) !== -1;
          if (r.time === hhmm && daysOk) {
            var key = r.id + "_" + now.toDateString() + "_" + hhmm;
            if (localStorage.getItem(lastFiredKey) === key) return;
            localStorage.setItem(lastFiredKey, key);
            new Notification("Время тренировки", { body: r.title });
            if (navigator.vibrate) navigator.vibrate([150, 80, 150]);
          }
        });
      })
      .catch(function () { /* сеть недоступна — тихо пропускаем */ });
  }

  checkReminders();
  setInterval(checkReminders, 20000);
})();
