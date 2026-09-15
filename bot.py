"""FireRiskBot — Telegram-бот для расчёта пожарной опасности по индексу Нестерова."""
import logging
import telebot

from config import (
    BOT_TOKEN, FIRMS_KEY, HISTORY_DAYS, FIRMS_DAYS, PRESET_REGIONS,
)
from fires import get_fires, count_fires
from nesterov import compute_nesterov
from storage import get_user_regions, add_user_region, remove_user_region
from weather import get_weather_merged

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)

HELP_TEXT = (
    "🔥 *FireRiskBot*\n\n"
    "Считаю пожарную опасность по индексу Нестерова "
    "на основе архивной погоды (Open-Meteo) и спутниковых очагов (NASA FIRMS).\n\n"
    "*Команды:*\n"
    "`/regions` — список доступных регионов\n"
    "`/fire <регион>` — расчёт по региону\n"
    "`/addregion <имя> <w,s,e,n>` — добавить свой регион (bbox)\n"
    "`/delregion <имя>` — удалить свой регион\n"
    "`/help` — эта справка\n\n"
    "*Пример:* `/fire mazowieckie`"
)


def _resolve_region(chat_id: int, name: str) -> tuple | None:
    name = name.strip().lower()
    if name in PRESET_REGIONS:
        return PRESET_REGIONS[name]
    user_regions = get_user_regions(chat_id)
    if name in user_regions:
        return tuple(user_regions[name])
    return None


@bot.message_handler(commands=["start", "help"])
def cmd_start(message):
    bot.send_message(message.chat.id, HELP_TEXT, parse_mode="Markdown")


@bot.message_handler(commands=["regions"])
def cmd_regions(message):
    presets = sorted(PRESET_REGIONS.keys())
    user = sorted(get_user_regions(message.chat.id).keys())

    text = "📍 *Пресеты:*\n" + "\n".join(f"• `{r}`" for r in presets)
    if user:
        text += "\n\n🛠 *Твои регионы:*\n" + "\n".join(f"• `{r}`" for r in user)
    text += "\n\nИспользование: `/fire <имя>`"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")


@bot.message_handler(commands=["fire"])
def cmd_fire(message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "Формат: `/fire <регион>`", parse_mode="Markdown")
        return

    name = parts[1].strip().lower()
    bbox = _resolve_region(message.chat.id, name)
    if bbox is None:
        bot.reply_to(message, f"Регион `{name}` не найден. Смотри `/regions`.", parse_mode="Markdown")
        return

    west, south, east, north = bbox
    lat = (south + north) / 2
    lon = (west + east) / 2

    bot.send_message(message.chat.id, f"📡 Считаю `{name}`…", parse_mode="Markdown")

    # Пожары
    fires_df = get_fires(west, south, east, north, FIRMS_KEY, days=FIRMS_DAYS)
    n_fires = count_fires(fires_df)

    # Погода + индекс
    weather = get_weather_merged(lat, lon, days=HISTORY_DAYS)
    index, risk_class, history = compute_nesterov(weather)

    # Средние показатели за период
    if not history.empty:
        avg_temp = history["temp"].mean()
        total_rain = history["rain"].sum()
        dry_days = (history["rain"] <= 3).sum()
    else:
        avg_temp = total_rain = dry_days = 0

    text = (
        f"🔥 *{name}*\n\n"
        f"*Очаги пожаров* (за {FIRMS_DAYS} дн.): `{n_fires}`\n"
        f"*Индекс Нестерова:* `{index:.0f}`\n"
        f"*Класс опасности:* *{risk_class}*\n\n"
        f"_Погода за {HISTORY_DAYS} дн.:_\n"
        f"• средняя T: `{avg_temp:.1f} °C`\n"
        f"• сумма осадков: `{total_rain:.1f} мм`\n"
        f"• сухих дней: `{dry_days}`"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")


@bot.message_handler(commands=["addregion"])
def cmd_addregion(message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(
            message,
            "Формат: `/addregion <имя> <w,s,e,n>`\nПример: `/addregion mycity 30.0,55.0,31.0,56.0`",
            parse_mode="Markdown",
        )
        return

    _, name, coords = parts
    name = name.strip().lower()
    try:
        w, s, e, n = [float(x) for x in coords.split(",")]
    except ValueError:
        bot.reply_to(message, "Координаты должны быть 4 числа через запятую: `w,s,e,n`", parse_mode="Markdown")
        return

    if not (-180 <= w < e <= 180) or not (-90 <= s < n <= 90):
        bot.reply_to(message, "Проверь координаты: w < e, s < n, широта [-90, 90], долгота [-180, 180].")
        return

    add_user_region(message.chat.id, name, (w, s, e, n))
    bot.reply_to(message, f"✅ Регион `{name}` добавлен.", parse_mode="Markdown")


@bot.message_handler(commands=["delregion"])
def cmd_delregion(message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "Формат: `/delregion <имя>`", parse_mode="Markdown")
        return
    name = parts[1].strip().lower()
    if remove_user_region(message.chat.id, name):
        bot.reply_to(message, f"🗑 Регион `{name}` удалён.", parse_mode="Markdown")
    else:
        bot.reply_to(message, f"Регион `{name}` не найден.", parse_mode="Markdown")


if __name__ == "__main__":
    log.info("FireRiskBot запущен")
    bot.infinity_polling()
