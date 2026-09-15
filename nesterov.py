"""Индекс Нестерова — накопительный расчёт пожарной опасности.

Формула: каждый сухой день (осадки < 3 мм) добавляем (T - Td) * T,
где T — температура в 15:00, Td — точка росы в 15:00.
День с осадками > 3 мм сбрасывает индекс в 0.
"""
import logging
import pandas as pd

from config import RISK_CLASSES

log = logging.getLogger(__name__)

RAIN_RESET_MM = 3.0
PEAK_HOUR = 15


def compute_nesterov(weather: pd.DataFrame) -> tuple[float, str, pd.DataFrame]:
    """Возвращает (индекс, класс, дневную таблицу с историей).

    weather: DataFrame с колонками time, temp, dew, rain.
    """
    if weather is None or weather.empty:
        return 0.0, "Нет данных", pd.DataFrame()

    df = weather.copy()
    df["hour"] = df["time"].dt.hour
    df["date"] = df["time"].dt.date

    # Берём 15:00 (или ближайший час, если ровно 15 нет)
    peak = df[df["hour"] == PEAK_HOUR].copy()
    if peak.empty:
        peak = df.loc[df.groupby("date")["hour"].apply(
            lambda h: (h - PEAK_HOUR).abs().idxmin()
        )].copy()

    daily_temp = peak.groupby("date").agg({"temp": "first", "dew": "first"}).reset_index()

    rain_daily = df.groupby("date")["rain"].sum().reset_index()
    rain_daily.columns = ["date", "rain_sum"]

    daily = daily_temp.merge(rain_daily, on="date", how="left").fillna(0)
    daily = daily.sort_values("date").reset_index(drop=True)

    index = 0.0
    history = []
    for _, row in daily.iterrows():
        t = float(row["temp"])
        td = float(row["dew"])
        rain = float(row["rain_sum"])

        if rain > RAIN_RESET_MM:
            index = 0.0
            event = "reset"
        else:
            index += (t - td) * t
            event = "add"

        history.append({
            "date": row["date"],
            "temp": t,
            "dew": td,
            "rain": rain,
            "index": index,
            "event": event,
        })

    return index, classify(index), pd.DataFrame(history)


def classify(index: float) -> str:
    for threshold, label in RISK_CLASSES:
        if index <= threshold:
            return label
    return RISK_CLASSES[-1][1]
