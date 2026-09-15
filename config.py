import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
FIRMS_KEY = os.getenv("FIRMS_KEY")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан в .env")
if not FIRMS_KEY:
    raise RuntimeError("FIRMS_KEY не задан в .env")

# --- Настройки ---
HISTORY_DAYS = 30          # за сколько дней считать индекс Нестерова
FIRMS_DAYS = 3             # за сколько дней тянуть очаги пожаров
REGIONS_FILE = "regions.json"

# --- Пресеты регионов (bbox = west, south, east, north) ---
PRESET_REGIONS = {
    # Польша
    "mazowieckie":        (20.429, 51.206, 21.772, 52.060),
    "slaskie":            (18.642, 50.275, 19.422, 50.996),
    "lodzkie":            (18.762, 51.060, 20.018, 52.291),
    "lubuskie":           (14.638, 51.524, 15.929, 52.925),
    "lubelskie":          (21.796, 50.305, 23.630, 52.121),
    "kujawsko-pomorskie": (17.303, 52.486, 19.513, 53.699),
    "pomorskie":          (16.807, 53.694, 19.306, 54.848),
    "wielkopolskie":      (15.906, 51.897, 17.471, 52.997),
    "warminsko-mazurskie":(19.229, 53.300, 21.199, 54.384),
    "zachodniopomorskie": (14.154, 53.030, 16.879, 54.572),
    "opolskie":           (17.530, 50.285, 18.570, 51.154),
    "podkarpackie":       (21.174, 49.429, 22.690, 50.290),
    "malopolskie":        (19.205, 49.597, 21.282, 50.202),
    "dolnoslaskie":       (15.815, 50.630, 17.297, 51.745),
    "swietokrzyskie":     (19.782, 50.502, 21.389, 51.205),
    "podlaskie":          (22.457, 52.370, 23.535, 54.325),
    # РФ (пример)
    "moscow-oblast":      (35.0, 54.0, 40.0, 57.0),
}

# Классы пожарной опасности по индексу Нестерова
RISK_CLASSES = [
    (300,   "I (Отсутствует)"),
    (1000,  "II (Малая)"),
    (4000,  "III (Средняя)"),
    (10000, "IV (Высокая)"),
    (float("inf"), "V (Чрезвычайная)"),
]
