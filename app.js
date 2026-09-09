// 1. Инициализация Telegram WebApp API
const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand(); // Разворачиваем окно на максимум
}

// 2. База расписания (0 - Понедельник ... 5 - Суббота)
const SCHEDULE_DATA = {
  0: [
    { start: "11:40", end: "13:00", name: "Комп'ютерна схемотехніка і електроніка", teacher: "Габузян Г.В." },
    { start: "13:10", end: "14:30", name: "Програмна інженерія", teacher: "Мілашенко А.М." },
    { start: "14:50", end: "16:10", name: "Комп'ютерна схемотехніка і електроніка", teacher: "Габузян Г.В." }
  ],
  1: [
    { start: "09:50", end: "11:00", name: "Методи та системи ШІ", teacher: "Мілашенко А.М." },
    { start: "11:20", end: "12:30", name: "Комп'ютерні системи", teacher: "Мурчкова М.М." },
    { start: "12:40", end: "13:50", name: "Методи та системи ШІ", teacher: "Мілашенко А.М." },
    { start: "14:55", end: "16:05", name: "Програмна інженерія", teacher: "Мілашенко А.М." }
  ],
  2: [
    { start: "10:00", end: "11:20", name: "Програмна інженерія", teacher: "Мілашенко А.М." },
    { start: "11:40", end: "13:00", name: "ОНС", teacher: "Хмарук Ю.С." },
    { start: "13:10", end: "14:30", name: "Комп'ютерна схемотехніка", teacher: "Габузян Г.В." },
    { start: "15:00", end: "16:20", name: "Архітектура комп'ютерів", teacher: "Мурчкова М.М." }
  ],
  3: [
    { start: "10:00", end: "11:20", name: "Комп'ютерні системи", teacher: "Мурчкова М.М." },
    { start: "11:40", end: "13:00", name: "Програмування", teacher: "Шинкаренко Л.М." },
    { start: "13:10", end: "14:30", name: "Програмування", teacher: "Шинкаренко Л.М." },
    { start: "14:50", end: "16:10", name: "ОНС", teacher: "" }
  ],
  4: [
    { start: "10:00", end: "11:20", name: "Програмна інженерія", teacher: "Мілашенко А.М." },
    { start: "11:40", end: "13:00", name: "Методи та системи ШІ", teacher: "Мілашенко А.М." },
    { start: "13:10", end: "14:30", name: "Фізичне виховання", teacher: "Коломоєць В.М." },
    { start: "14:50", end: "16:10", name: "Українська мова за ПС", teacher: "Петрухненко В.В." }
  ],
  5: [
    { start: "10:00", end: "11:20", name: "Комп'ютерні системи / Фізвиховання", teacher: "" },
    { start: "11:40", end: "13:00", name: "Архітектура комп'ютерів", teacher: "Мурчкова М.М." },
    { start: "13:10", end: "14:30", name: "Комп'ютерна схемотехніка", teacher: "" },
    { start: "14:50", end: "16:10", name: "ШІ / Українська мова", teacher: "" }
  ]
};

// 3. Apple Taptic Engine (вибрация при кликах)
function hapticFeedback(style = 'light') {
  if (tg?.HapticFeedback) {
    tg.HapticFeedback.impactOccurred(style);
  }
}

// 4. Переключение Тем (Dark / Light)
function toggleTheme() {
  hapticFeedback('medium');
  const root = document.documentElement;
  const isDark = root.getAttribute("data-theme") === "dark";
  const newTheme = isDark ? "light" : "dark";
  
  root.setAttribute("data-theme", newTheme);
  document.getElementById("themeBtn").innerText = isDark ? "☀️" : "🌙";
}

// 5. Отрисовка списка пар по выбранному дню
function selectDay(dayIndex) {
  hapticFeedback('light');
  
  // Переключение активного таба
  const chips = document.querySelectorAll(".day-chip");
  chips.forEach((c, idx) => c.classList.toggle("active", idx === dayIndex));

  const container = document.getElementById("scheduleListContainer");
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

    // Расчет длины перемены между парами
    if (i < pairs.length - 1) {
      const [h1, m1] = pair.end.split(":").map(Number);
      const [h2, m2] = pairs[i + 1].start.split(":").map(Number);
      const diff = (h2 * 60 + m2) - (h1 * 60 + m1);
      html += `<div class="break-row">⏳ Перерва ${diff} хв</div>`;
    }
  });

  container.innerHTML = html;
}

// 6. Динамический таймер: определение текущей пары и прогресса
function updateLiveWidget() {
  const now = new Date();
  const currentMinutes = now.getHours() * 60 + now.getMinutes();
  const todayDay = now.getDay();
  const todayIndex = todayDay === 0 ? 6 : todayDay - 1; // 0: Пн ... 6: Вс
  
  const pairs = SCHEDULE_DATA[todayIndex] || [];
  const statusEl = document.getElementById("liveStatus");
  const nameEl = document.getElementById("livePairName");
  const metaEl = document.getElementById("livePairMeta");
  const progressEl = document.getElementById("pairProgress");

  if (pairs.length === 0) {
    statusEl.innerText = "Сьогодні вихідний";
    nameEl.innerText = "Пар немає";
    metaEl.innerText = "Гарного відпочинку!";
    progressEl.style.width = "0%";
    return;
  }

  // Проверяем каждую пару
  for (let i = 0; i < pairs.length; i++) {
    const pair = pairs[i];
    const [hStart, mStart] = pair.start.split(":").map(Number);
    const [hEnd, mEnd] = pair.end.split(":").map(Number);
    const startMins = hStart * 60 + mStart;
    const endMins = hEnd * 60 + mEnd;

    // Пара идет прямо сейчас
    if (currentMinutes >= startMins && currentMinutes < endMins) {
      statusEl.innerText = "Зараз іде пара";
      nameEl.innerText = pair.name;
      metaEl.innerText = `${pair.start} – ${pair.end} • ${pair.teacher || 'Викладач не вказаний'}`;
      
      const percent = ((currentMinutes - startMins) / (endMins - startMins)) * 100;
      progressEl.style.width = `${Math.round(percent)}%`;
      return;
    }

    // Скоро начнется следующая пара
    if (currentMinutes < startMins) {
      statusEl.innerText = "Наступна пара";
      nameEl.innerText = pair.name;
      const leftMins = startMins - currentMinutes;
      metaEl.innerText = `Початок о ${pair.start} (через ${leftMins} хв)`;
      progressEl.style.width = "0%";
      return;
    }
  }

  // Если все пары на сегодня закончились
  statusEl.innerText = "Навчальний день завершено";
  nameEl.innerText = "Всі пари закінчилися";
  metaEl.innerText = "Час для власних справ";
  progressEl.style.width = "100%";
}

// 7. Точка старта при загрузке страницы
document.addEventListener("DOMContentLoaded", () => {
  const today = new Date().getDay();
  const dayIndex = today === 0 ? 0 : today - 1; // если воскресенье — покажем понедельник
  selectDay(Math.min(dayIndex, 5));
  
  updateLiveWidget();
  // Пересчитываем статус каждые 30 секунд
  setInterval(updateLiveWidget, 30000);
});
