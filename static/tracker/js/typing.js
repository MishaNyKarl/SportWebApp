(function () {
  "use strict";

  var WORDS = [
    "the", "of", "and", "a", "to", "in", "is", "you", "that", "it",
    "he", "was", "for", "on", "are", "as", "with", "his", "they", "at",
    "be", "this", "have", "from", "or", "one", "had", "by", "word", "but",
    "not", "what", "all", "were", "we", "when", "your", "can", "said", "there",
    "use", "each", "which", "she", "how", "their", "if", "will", "up", "other",
    "about", "out", "many", "then", "them", "these", "so", "some", "her", "would",
    "make", "like", "him", "into", "time", "has", "look", "two", "more", "write",
    "see", "number", "way", "could", "people", "than", "first", "water", "been", "call",
    "who", "am", "its", "now", "find", "long", "down", "day", "did", "get",
    "come", "made", "may", "part", "over", "new", "sound", "take", "only", "little",
    "work", "know", "place", "year", "live", "back", "give", "most", "very", "after",
    "thing", "our", "just", "name", "good", "sentence", "man", "think", "great", "help",
    "low", "line", "before", "turn", "cause", "same", "mean", "differ", "move", "right",
    "boy", "old", "too", "does", "tell", "sentence", "set", "three", "want", "air",
    "well", "also", "play", "small", "end", "put", "home", "read", "hand", "port",
    "large", "spell", "add", "even", "land", "here", "must", "big", "high", "such",
    "follow", "act", "why", "ask", "men", "change", "went", "light", "kind", "off",
    "need", "house", "picture", "try", "us", "again", "animal", "point", "mother", "world",
  ];

  var DURATIONS = [15, 30, 60, 120];

  var wordsEl = document.getElementById("type-words");
  var input = document.getElementById("type-input");
  var timeEl = document.getElementById("type-time");
  var wpmEl = document.getElementById("type-wpm");
  var chipsEl = document.getElementById("duration-chips");
  var btnRestart = document.getElementById("btn-type-restart");
  var btnAgain = document.getElementById("btn-type-again");
  var testBox = document.getElementById("type-test-box");
  var resultBox = document.getElementById("type-result-box");

  if (!wordsEl || !input) return;

  var duration = 30;
  var words = [];
  var typedWords = [];
  var wordIndex = 0;
  var startTime = null;
  var timerId = null;
  var timeLeft = duration;
  var finished = false;

  function escapeHtml(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function genWords(n) {
    var arr = [];
    for (var i = 0; i < n; i++) arr.push(WORDS[Math.floor(Math.random() * WORDS.length)]);
    return arr;
  }

  function renderWord(w, t, isCurrent) {
    var len = Math.max(w.length, t.length);
    var html = "";
    for (var c = 0; c < len; c++) {
      var caret = isCurrent && c === t.length ? '<span class="type-caret"></span>' : "";
      if (c < w.length && c < t.length) {
        html += caret + '<span class="type-char ' + (w[c] === t[c] ? "correct" : "incorrect") + '">' + escapeHtml(w[c]) + "</span>";
      } else if (c < w.length) {
        html += caret + '<span class="type-char">' + escapeHtml(w[c]) + "</span>";
      } else {
        html += caret + '<span class="type-char extra">' + escapeHtml(t[c]) + "</span>";
      }
    }
    if (isCurrent && t.length >= len) html += '<span class="type-caret"></span>';
    return html;
  }

  function render() {
    var html = "";
    for (var i = 0; i < words.length; i++) {
      var w = words[i];
      var isCurrent = i === wordIndex;
      var isDone = i < wordIndex;
      html += '<span class="type-word' + (isCurrent ? " current" : "") + '">';
      if (isDone) {
        html += renderWord(w, typedWords[i] || "", false);
      } else if (isCurrent) {
        html += renderWord(w, input.value, true);
      } else {
        html += escapeHtml(w).split("").map(function (ch) {
          return '<span class="type-char">' + ch + "</span>";
        }).join("");
      }
      html += "</span> ";
    }
    wordsEl.innerHTML = html;

    var currentEl = wordsEl.querySelector(".type-word.current");
    if (currentEl) {
      var box = wordsEl.getBoundingClientRect();
      var el = currentEl.getBoundingClientRect();
      if (el.top - box.top > box.height - 40) {
        wordsEl.scrollTop += el.top - box.top - 20;
      }
    }
  }

  function updateLiveStats() {
    timeEl.textContent = Math.ceil(timeLeft);
    var elapsedMin = startTime ? (Date.now() - startTime) / 60000 : 0;
    var correctChars = 0;
    for (var i = 0; i < wordIndex; i++) {
      if (words[i] === typedWords[i]) correctChars += words[i].length + 1;
    }
    wpmEl.textContent = elapsedMin > 0 ? Math.round(correctChars / 5 / elapsedMin) : 0;
  }

  function tick() {
    var elapsed = (Date.now() - startTime) / 1000;
    timeLeft = Math.max(0, duration - elapsed);
    updateLiveStats();
    if (timeLeft <= 0) finish();
  }

  function finish() {
    if (finished) return;
    finished = true;
    clearInterval(timerId);
    input.disabled = true;
    typedWords[wordIndex] = input.value;

    var correct = 0, incorrect = 0, extra = 0, totalTyped = 0;
    for (var i = 0; i <= wordIndex && i < words.length; i++) {
      var w = words[i], t = typedWords[i] || "";
      var len = Math.max(w.length, t.length);
      for (var c = 0; c < len; c++) {
        if (c < w.length && c < t.length) { if (w[c] === t[c]) correct++; else incorrect++; }
        else if (c < w.length) incorrect++;
        else extra++;
      }
      totalTyped += t.length;
    }

    var minutes = duration / 60;
    var netWpm = Math.round(correct / 5 / minutes);
    var rawWpm = Math.round(totalTyped / 5 / minutes);
    var accuracy = totalTyped > 0 ? Math.round((correct / totalTyped) * 100) : 100;

    document.getElementById("result-wpm").textContent = netWpm;
    document.getElementById("result-acc").textContent = accuracy + "%";
    document.getElementById("result-raw").textContent = rawWpm;
    document.getElementById("result-time").textContent = duration + "s";

    testBox.style.display = "none";
    resultBox.style.display = "";
  }

  function reset() {
    clearInterval(timerId);
    words = genWords(200);
    typedWords = [];
    wordIndex = 0;
    startTime = null;
    timeLeft = duration;
    finished = false;
    input.value = "";
    input.disabled = false;
    timeEl.textContent = duration;
    wpmEl.textContent = "0";
    resultBox.style.display = "none";
    testBox.style.display = "";
    render();
    input.focus();
  }

  input.addEventListener("input", function () {
    if (finished) return;
    if (startTime === null) {
      startTime = Date.now();
      timerId = setInterval(tick, 200);
    }
    var val = input.value;
    if (val === " ") { input.value = ""; return; }
    if (val.endsWith(" ")) {
      typedWords[wordIndex] = val.slice(0, -1);
      wordIndex += 1;
      input.value = "";
      if (wordIndex >= words.length - 20) words = words.concat(genWords(100));
    }
    render();
    updateLiveStats();
  });

  wordsEl.addEventListener("click", function () { input.focus(); });

  if (chipsEl) {
    chipsEl.addEventListener("click", function (e) {
      var chip = e.target.closest(".chip");
      if (!chip) return;
      Array.prototype.forEach.call(chipsEl.querySelectorAll(".chip"), function (c) {
        c.classList.remove("active");
      });
      chip.classList.add("active");
      duration = parseInt(chip.dataset.sec, 10);
      reset();
    });
  }

  if (btnRestart) btnRestart.addEventListener("click", reset);
  if (btnAgain) btnAgain.addEventListener("click", reset);

  reset();

  // --- Реальная статистика аккаунта MonkeyType ---
  var statsBox = document.getElementById("monkeytype-stats-box");
  if (statsBox && window.MONKEYTYPE_CONNECTED && window.TYPING_STATS_URL) {
    fetch(window.TYPING_STATS_URL)
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (!data.ok || !data.stats) {
          statsBox.innerHTML = '<div class="empty-state"><div class="emoji">⚠️</div><div>' +
            (data.errors && data.errors[0] ? escapeHtml(data.errors[0]) : "Не удалось получить статистику") +
            "</div></div>";
          return;
        }
        var s = data.stats;
        var pb60 = data.personalBests && data.personalBests.time60;
        var hours = (s.timeTyping / 3600).toFixed(1);
        var html = '<div class="stat-grid">' +
          '<div class="stat-tile accent-blue"><div class="value">' + (pb60 ? Math.round(pb60.wpm) : "—") + '</div><div class="label">Лучший WPM, 60с</div></div>' +
          '<div class="stat-tile accent-green"><div class="value">' + (pb60 ? Math.round(pb60.acc) + "%" : "—") + '</div><div class="label">Точность (best)</div></div>' +
          '<div class="stat-tile accent-orange"><div class="value">' + s.completedTests + '</div><div class="label">Тестов пройдено</div></div>' +
          '<div class="stat-tile accent-purple"><div class="value">' + hours + '</div><div class="label">Часов набора</div></div>' +
          "</div>";
        if (data.streak) {
          html += '<p class="muted text-center" style="margin-top:10px">🔥 Серия: ' + data.streak.length +
            ' дн. (макс ' + data.streak.maxLength + ')</p>';
        }
        statsBox.innerHTML = html;
      })
      .catch(function () {
        statsBox.innerHTML = '<div class="empty-state"><div class="emoji">⚠️</div><div>Ошибка сети при обращении к MonkeyType</div></div>';
      });
  }
})();
