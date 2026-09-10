// ==========================================
// 1. Ініціалізація Telegram WebApp API
// ==========================================
const tg = window.Telegram?.WebApp;

if (tg) {
  tg.ready();
  tg.expand(); // Відкриваємо застосунок на весь екран

  // Налаштування нативної нижньої кнопки Telegram
  if (tg.MainButton) {
    tg.MainButton.setText("💬 Керування ботом та сповіщеннями");
    tg.MainButton.show();
    tg.MainButton.onClick(() => {
      hapticFeedback('medium');
      tg.close(); // Плавно згортає WebApp і повертає юзера в чат з ботом
    });
  }
}

// Функція виходу в чат для кастомних кнопок та віджетів
function closeToChat() {
  hapticFeedback('light');
  if (tg) tg.close();
}

// ==========================================
// 2. Тактильний відгук (Taptic Engine)
// ==========================================
function hapticFeedback(style = 'light') {
  if (tg?.HapticFeedback) {
    tg.HapticFeedback.impactOccurred(style);
  }
}

// ==========================================
// 3. База даних розкладу (0 - Пн ... 5 - Сб)
// ==========================================
const SCHEDULE_DATA = {
  0: [
    {
      start: "10:40",
      end: "12:00",
      name: "1. Комп'ютерна схемотехніка і електроніка",
      teacher: "Габузян Г.В."
    },
    {
      start: "13:50",
      end: "15:10",
      name: "3. Комп'ютерна схемотехніка і електроніка",
      teacher: "Габузян Г.В."
    },
    {
      start: "15:20",
      end: "16:40",
      name: "4. Програмна інженерія",
      teacher: "Мілашенко А.М."
    }
  ],
  1: [
    {
      start: "10:40",
      end: "12:00",
      name: "1. Програмна інженерія",
      teacher: "Мілашенко А.М."
    },
    {
      start: "12:15",
      end: "13:35",
      name: "2. Методи та системи штучного інтелекту",
      teacher: "Мілашенко А.М."
    },
    {
      start: "13:50",
      end: "15:10",
      name: "3. Комп'ютерні системи",
      teacher: "Мурчкова М.М."
    },
    {
      start: "15:20",
      end: "16:40",
      name: "4. Методи та системи штучного інтелекту",
      teacher: "Мілашенко А.М."
    }
  ],
  2: [
    {
      start: "10:40",
      end: "12:00",
      name: "1. Архітектура комп'ютерів",
      teacher: "Мурчкова М.М."
    },
    {
      start: "12:15",
      end: "13:35",
      name: "2. Програмна інженерія",
      teacher: "Мілашенко А.М."
    },
    {
      start: "13:50",
      end: "15:10",
      name: "3. [Чис] ОНС / [Знам] Комп'ютерні системи",
      teacher: "Хмарук Ю.С. / Мурчкова М.М."
    },
    {
      start: "15:20",
      end: "16:40",
      name: "4. Комп'ютерна схемотехніка і електроніка",
      teacher: "Габузян Г.В."
    }
  ],
  3: [
    {
      start: "10:40",
      end: "12:00",
      name: "1. Програмування",
      teacher: "Шинкаренко Л.М."
    },
    {
      start: "12:15",
      end: "13:35",
      name: "2. [Чис] ОНС / [Знам] Методи та системи ШІ",
      teacher: "Мілашенко А.М."
    },
    {
      start: "13:50",
      end: "15:10",
      name: "3. Комп'ютерні системи",
      teacher: "Мурчкова М.М."
    },
    {
      start: "15:20",
      end: "16:40",
      name: "4. Програмування",
      teacher: "Шинкаренко Л.М."
    }
  ],
  4: [
    {
      start: "10:40",
      end: "12:00",
      name: "1. Українська мова за ПС",
      teacher: "Петрухненко В.В."
    },
    {
      start: "12:15",
      end: "13:35",
      name: "2. Програмна інженерія",
      teacher: "Мілашенко А.М."
    },
    {
      start: "13:50",
      end: "15:10",
      name: "3. Методи та системи штучного інтелекту",
      teacher: "Мілашенко А.М."
    },
    {
      start: "15:20",
      end: "16:40",
      name: "4. Фізичне виховання",
      teacher: "Коломоєць В.М."
    }
  ],
  5: [
    {
      start: "10:40",
      end: "12:00",
      name: "1. [Чис] Методи та системи ШІ / [Знам] Укр. мова",
      teacher: "Мілашенко / Петрухненко"
    },
    {
      start: "12:15",
      end: "13:35",
      name: "2. [Чис] Комп'ютерні системи / [Знам] Укр. мова / Фіз-ра",
      teacher: "—"
    },
    {
      start: "13:50",
      end: "15:10",
      name: "3. Архітектура комп'ютерів",
      teacher: "Мурчкова М.М."
    },
    {
      start: "15:20",
      end: "16:40",
      name: "4. [Чис] Комп'ютерна схемотехніка / [Знам] Укр. мова",
      teacher: "Петрухненко В.В."
    }
  ]
};

// ==========================================
// 4. Перемикання Тем (Dark / Light)
// ==========================================
function toggleTheme() {
  hapticFeedback('medium');
  const root = document.documentElement;
  const isDark = root.getAttribute("data-theme") === "dark";
  const newTheme = isDark ? "light" : "dark";

  root.setAttribute("data-theme", newTheme);
  const themeBtn = document.getElementById("themeBtn");
  if (themeBtn) {
    themeBtn.innerText = isDark ? "☀️" : "🌙";
  }
}

// ==========================================
// 5. Відображення розкладу для обраного дня
// ==========================================
function selectDay(dayIndex) {
  hapticFeedback('light');

  const chips = document.querySelectorAll(".day-chip");
  chips.forEach((c, idx) => c.classList.toggle("active", idx === dayIndex));

  const container = document.getElementById("scheduleListContainer");
  if (!container) return;

  const pairs = SCHEDULE_DATA[dayIndex] || [];

  if (pairs.length === 0) {
    container.innerHTML = '<div style="text-align:center; padding: 25px; color: var(--text-sub);">🎉 Вихідний день! Пар немає.</div>';
    return;
  }

  let html = "";
  pairs.forEach((pair, i) => {
    html += `
      <div class="pair-row" onclick="hapticFeedback('light')">
        <div class="pair-time">${pair.start} - ${pair.end}</div>
        <div class="pair-info">
          <div class="pair-name">${pair.name}</div>
          <div class="pair-teacher">${pair.teacher || '—'}</div>
        </div>
      </div>
    `;

    // Розрахунок тривалості перерви між парами
    if (i < pairs.length - 1) {
      const [h1, m1] = pair.end.split(":").map(Number);
      const [h2, m2] = pairs[i + 1].start.split(":").map(Number);
      const diff = (h2 * 60 + m2) - (h1 * 60 + m1);
      html += `<div class="break-row">⏳ Перерва ${diff} хв</div>`;
    }
  });

  container.innerHTML = html;
}

// ==========================================
// 6. Реальний час: таймер та статус поточної пари
// ==========================================
function updateLiveWidget() {
  const now = new Date();
  const currentMinutes = now.getHours() * 60 + now.getMinutes();
  const todayDay = now.getDay();
  // 0 - Неділя, 1 - Пн ... 6 - Сб -> індекси 0 (Пн) ... 5 (Сб)
  const todayIndex = todayDay === 0 ? 6 : todayDay - 1;

  const pairs = SCHEDULE_DATA[todayIndex] || [];
  const statusEl = document.getElementById("liveStatus");
  const nameEl = document.getElementById("livePairName");
  const metaEl = document.getElementById("livePairMeta");
  const progressEl = document.getElementById("pairProgress");

  if (!statusEl || !nameEl || !metaEl || !progressEl) return;

  if (pairs.length === 0) {
    statusEl.innerText = "Сьогодні вихідний";
    nameEl.innerText = "Пар немає";
    metaEl.innerText = "Гарного відпочинку!";
    progressEl.style.width = "0%";
    return;
  }

  for (let i = 0; i < pairs.length; i++) {
    const pair = pairs[i];
    const [hStart, mStart] = pair.start.split(":").map(Number);
    const [hEnd, mEnd] = pair.end.split(":").map(Number);
    const startMins = hStart * 60 + mStart;
    const endMins = hEnd * 60 + mEnd;

    // Пара йде зараз
    if (currentMinutes >= startMins && currentMinutes < endMins) {
      statusEl.innerText = "Зараз іде пара";
      nameEl.innerText = pair.name;
      metaEl.innerText = `${pair.start} – ${pair.end} • ${pair.teacher || 'Викладач не вказаний'}`;

      const percent = ((currentMinutes - startMins) / (endMins - startMins)) * 100;
      progressEl.style.width = `${Math.round(percent)}%`;
      return;
    }

    // Очікування наступної пари
    if (currentMinutes < startMins) {
      statusEl.innerText = "Наступна пара";
      nameEl.innerText = pair.name;
      const leftMins = startMins - currentMinutes;
      metaEl.innerText = `Початок о ${pair.start} (через ${leftMins} хв)`;
      progressEl.style.width = "0%";
      return;
    }
  }

  // Всі пари завершилися
  statusEl.innerText = "Навчальний день завершено";
  nameEl.innerText = "Всі пари закінчилися";
  metaEl.innerText = "Час для власних справ";
  progressEl.style.width = "100%";
}

// ==========================================
// 7. Точка входу
// ==========================================
document.addEventListener("DOMContentLoaded", () => {
  const today = new Date().getDay();
  const dayIndex = today === 0 ? 0 : today - 1;
  selectDay(Math.min(dayIndex, 5));

  updateLiveWidget();
  setInterval(updateLiveWidget, 30000);
});
