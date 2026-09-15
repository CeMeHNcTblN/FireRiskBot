# 🔥 FireRiskBot — Fire Danger Estimation via Satellite & Weather Data

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4)
![NASA FIRMS](https://img.shields.io/badge/NASA-FIRMS-red)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

A Telegram bot that estimates **fire danger** for any region using the **Nesterov index**, based on:

- 📡 **NASA FIRMS** — satellite-detected fire hotspots (VIIRS SNPP)
- 🌡 **Open-Meteo** — historical weather (ERA5 archive + forecast)
- 🧮 **Nesterov accumulation** — daily dry-day temperature sums with rain reset

> ⚠️ This is a **rough estimation**, not a fire-danger forecast. See [Limitations](#-limitations).

---

## ✨ Features

- 🌍 **Any region** — 16 presets (Polish voivodeships + Moscow region) + add your own by bounding box
- 🛰 **Satellite fire detection** — NASA FIRMS VIIRS hotspots for the last N days
- 🌦 **Archive weather** — Open-Meteo ERA5 (30+ days of real history, not forecast)
- 🧮 **Nesterov index** — proper accumulation with rain-based reset
- 🏷 **5 fire-danger classes** — from I (absent) to V (extreme)
- 💾 **Per-user regions** — each user has their own list (regions.json)

---

## 🏗️ Architecture

```
Telegram user
     │  /fire <region>
     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   bot.py     │──▶ │  weather.py  │──▶ │  Open-Meteo  │
│  (Telebot)   │    │  (ERA5+fcst) │    │   Archive    │
└──────┬───────┘    └──────────────┘    └──────────────┘
       │
       │            ┌──────────────┐    ┌──────────────┐
       └──────────▶ │   fires.py   │──▶ │  NASA FIRMS  │
       │            │   (VIIRS)    │    │   Area API   │
       │            └──────────────┘    └──────────────┘
       ▼
┌──────────────┐
│ nesterov.py  │  index + class + history
└──────────────┘
```

**Pipeline:**
1. Resolve region → bounding box
2. Fetch fire hotspots from FIRMS for `FIRMS_DAYS` days
3. Fetch weather for `HISTORY_DAYS` days (archive + recent)
4. Compute Nesterov index day by day (reset on rain > 3 mm)
5. Classify into one of 5 risk classes
6. Send report

---

## 🚀 Quick Start

### 1. Clone

```bash
git clone https://github.com/<your-username>/firerisk-bot.git
cd firerisk-bot
```

### 2. Virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Get API keys

- **Telegram bot token** — [@BotFather](https://t.me/BotFather) → `/newbot`
- **NASA FIRMS MAP_KEY** — generate at [firms.modaps.eosdis.nasa.gov/api/map_key](https://firms.modaps.eosdis.nasa.gov/api/map_key/). The key arrives by email instantly. **Important:** only keys from this page work with the FIRMS Area API; Earthdata profile keys will be rejected.

### 5. Configure `.env`

```bash
cp .env.example .env
```

```env
BOT_TOKEN=your_token
FIRMS_KEY=your_firms_key
```

### 6. Run

```bash
python bot.py
```

Open the bot in Telegram → `/start`.

---

## 🤖 Bot Commands

| Command | Description |
|---|---|
| `/start` `/help` | Help |
| `/regions` | List preset + custom regions |
| `/fire <name>` | Run fire-danger analysis |
| `/addregion <name> <w,s,e,n>` | Add custom region by bbox |
| `/delregion <name>` | Remove custom region |

### Example

```
/addregion mycity 30.0,55.0,31.0,56.0
/fire mycity
```

Response:

```
🔥 mycity

Очаги пожаров (за 3 дн.): 2
Индекс Нестерова: 1450
Класс опасности: III (Средняя)

Погода за 30 дн.:
• средняя T: 18.4 °C
• сумма осадков: 42.1 мм
• сухих дней: 21
```

---

## 🧮 How Nesterov Index Works

The Nesterov index accumulates daily dryness:

```
if rain_today > 3 mm:
    index = 0
else:
    index += (T_15 - Td_15) * T_15
```

Where `T_15` is temperature at 15:00 and `Td_15` is dew point at 15:00.

**Risk classes:**

| Index | Class |
|---|---|
| 0 – 300 | I (Absent) |
| 301 – 1000 | II (Low) |
| 1001 – 4000 | III (Moderate) |
| 4001 – 10000 | IV (High) |
| > 10000 | V (Extreme) |

---

## 📂 Project Structure

```
firerisk-bot/
├── .env                 # secrets (gitignored)
├── .env.example
├── .gitignore
├── requirements.txt
├── config.py            # regions, thresholds
├── weather.py           # Open-Meteo wrapper
├── fires.py             # NASA FIRMS wrapper
├── nesterov.py          # index computation
├── storage.py           # per-user regions
├── bot.py               # Telegram entrypoint
└── README.md
```

---

## ⚠️ Limitations

- **Nesterov is a proxy**, not a real fire forecast. It uses only temperature and dew point.
- **ERA5 reanalysis has ~5-day lag.** The most recent days come from Forecast API, which is a model output, not observations.
- **FIRMS has a transaction limit** (5000 per 10 minutes per key). Heavy use may temporarily block the key.
- **Bounding boxes are rectangles**, not real administrative borders.
- **Cloud cover and satellite overpass** affect hotspot detection — not every fire is registered.
- **VIIRS SNPP NRT** data is near-real-time and may be revised later.

---

## 🛣️ Roadmap

- [ ] Real GeoJSON polygons instead of bboxes
- [ ] Chart of index history (matplotlib → Telegram photo)
- [ ] Map of hotspots (folium)
- [ ] Multi-day forecast mode
- [ ] SQLite for historical runs
- [ ] Docker image
- [ ] CI (GitHub Actions)

---

## 🧰 Tech Stack

- [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI)
- [Open-Meteo](https://open-meteo.com/) — archive + forecast
- [NASA FIRMS](https://firms.modaps.eosdis.nasa.gov/) — VIIRS hotspots
- [pandas](https://pandas.pydata.org/) + [numpy](https://numpy.org/)
- [requests-cache](https://github.com/requests-cache/requests-cache) + [retry-requests](https://github.com/jd/tenacity)

---

## 📜 License

MIT — see [LICENSE](LICENSE).

---
---

# 🔥 FireRiskBot — расчёт пожарной опасности по спутникам и погоде

Telegram-бот, который оценивает **пожарную опасность** для любого региона по **индексу Нестерова**, используя:

- 📡 **NASA FIRMS** — спутниковые очаги пожаров (VIIRS SNPP)
- 🌡 **Open-Meteo** — архивная погода (ERA5) + прогноз
- 🧮 **Накопление Нестерова** — сухие дни суммируются, дождь сбрасывает

> ⚠️ Это **грубая оценка**, а не прогноз пожарной опасности. См. [Ограничения](#-ограничения-1).

---

## ✨ Возможности

- 🌍 **Любой регион** — 16 пресетов (воеводства Польши + Московская область) + свои по bbox
- 🛰 **Спутниковые очаги** — NASA FIRMS VIIRS за последние N дней
- 🌦 **Архивная погода** — Open-Meteo ERA5 (30+ дней реальной истории)
- 🧮 **Индекс Нестерова** — правильное накопление со сбросом при осадках
- 🏷 **5 классов опасности** — от I (отсутствует) до V (чрезвычайная)
- 💾 **Свои регионы у каждого** — `regions.json`

---

## 🏗️ Архитектура

```
Пользователь Telegram
     │  /fire <регион>
     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   bot.py     │──▶ │  weather.py  │──▶ │  Open-Meteo  │
│  (Telebot)   │    │  (ERA5+fcst) │    │   Archive    │
└──────┬───────┘    └──────────────┘    └──────────────┘
       │
       │            ┌──────────────┐    ┌──────────────┐
       └──────────▶ │   fires.py   │──▶ │  NASA FIRMS  │
       │            │   (VIIRS)    │    │   Area API   │
       │            └──────────────┘    └──────────────┘
       ▼
┌──────────────┐
│ nesterov.py  │  индекс + класс + история
└──────────────┘
```

**Пайплайн:**
1. Регион → bounding box
2. Очаги пожаров из FIRMS за `FIRMS_DAYS`
3. Погода за `HISTORY_DAYS` (архив + свежие)
4. Индекс Нестерова по дням (сброс при дожде > 3 мм)
5. Класс опасности (I–V)
6. Отчёт в Telegram

---

## 🚀 Быстрый старт

### 1. Клонировать

```bash
git clone https://github.com/<твой-ник>/firerisk-bot.git
cd firerisk-bot
```

### 2. Виртуальное окружение

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Установить зависимости

```bash
pip install -r requirements.txt
```

### 4. Получить ключи

- **Telegram токен** — [@BotFather](https://t.me/BotFather) → `/newbot`
- **NASA FIRMS MAP_KEY** — генерируй на [firms.modaps.eosdis.nasa.gov/api/map_key](https://firms.modaps.eosdis.nasa.gov/api/map_key/). Ключ приходит на почту мгновенно. **Важно:** с FIRMS Area API работают только ключи с этой страницы; ключи из профиля Earthdata будут отклонены.

### 5. Настроить `.env`

```bash
cp .env.example .env
```

```env
BOT_TOKEN=твой_токен
FIRMS_KEY=твой_ключ
```

### 6. Запустить

```bash
python bot.py
```

Открой бота в Telegram → `/start`.

---

## 🤖 Команды бота

| Команда | Описание |
|---|---|
| `/start` `/help` | Справка |
| `/regions` | Список регионов (пресеты + свои) |
| `/fire <имя>` | Расчёт пожароопасности |
| `/addregion <имя> <w,s,e,n>` | Добавить регион по bbox |
| `/delregion <имя>` | Удалить свой регион |

### Пример

```
/addregion mycity 30.0,55.0,31.0,56.0
/fire mycity
```

Ответ:

```
🔥 mycity

Очаги пожаров (за 3 дн.): 2
Индекс Нестерова: 1450
Класс опасности: III (Средняя)

Погода за 30 дн.:
• средняя T: 18.4 °C
• сумма осадков: 42.1 мм
• сухих дней: 21
```

---

## 🧮 Как работает индекс Нестерова

Индекс накапливает «сухость» по дням:

```
если осадки > 3 мм:
    индекс = 0
иначе:
    индекс += (T_15 - Td_15) * T_15
```

Где `T_15` — температура в 15:00, `Td_15` — точка росы в 15:00.

**Классы опасности:**

| Индекс | Класс |
|---|---|
| 0 – 300 | I (Отсутствует) |
| 301 – 1000 | II (Малая) |
| 1001 – 4000 | III (Средняя) |
| 4001 – 10000 | IV (Высокая) |
| > 10000 | V (Чрезвычайная) |

---

## 📂 Структура проекта

```
firerisk-bot/
├── .env                 # секреты (gitignored)
├── .env.example
├── .gitignore
├── requirements.txt
├── config.py            # регионы, пороги
├── weather.py           # Open-Meteo
├── fires.py             # NASA FIRMS
├── nesterov.py          # индекс
├── storage.py           # регионы пользователей
├── bot.py               # Telegram
└── README.md
```

---

## ⚠️ Ограничения

- **Индекс Нестерова — это прокси**, а не реальный прогноз. Только температура и точка росы.
- **ERA5 имеет задержку ~5 дней.** Свежие дни берутся из Forecast API — это вывод модели, а не наблюдения.
- **У FIRMS есть лимит транзакций** (5000 за 10 минут на ключ).
- **Bounding box — прямоугольник**, а не реальные границы региона.
- **Облачность и пролёт спутника** влияют на детекцию очагов.
- **VIIRS SNPP NRT** — near-real-time, данные могут уточняться.

---

## 🛣️ Планы

- [ ] Реальные GeoJSON-полигоны вместо bbox
- [ ] График истории индекса (matplotlib → фото в Telegram)
- [ ] Карта очагов (folium)
- [ ] Многодневный прогноз
- [ ] SQLite для исторических прогонов
- [ ] Docker-образ
- [ ] CI (GitHub Actions)

---

## 🧰 Стек

- [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI)
- [Open-Meteo](https://open-meteo.com/) — архив + прогноз
- [NASA FIRMS](https://firms.modaps.eosdis.nasa.gov/) — VIIRS
- [pandas](https://pandas.pydata.org/) + [numpy](https://numpy.org/)
- [requests-cache](https://github.com/requests-cache/requests-cache) + [retry-requests](https://github.com/jd/tenacity)

---

## 📜 Лицензия

MIT — см. [LICENSE](LICENSE).
