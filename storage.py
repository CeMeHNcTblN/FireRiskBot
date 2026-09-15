"""Пользовательские регионы: {chat_id: {name: [w, s, e, n]}}."""
import json
import os
import logging

from config import REGIONS_FILE

log = logging.getLogger(__name__)


def _load() -> dict:
    if not os.path.exists(REGIONS_FILE):
        return {}
    try:
        with open(REGIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        log.warning("Не удалось прочитать %s: %s", REGIONS_FILE, e)
        return {}


def _save(data: dict) -> None:
    with open(REGIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_user_regions(chat_id: int) -> dict:
    return _load().get(str(chat_id), {})


def add_user_region(chat_id: int, name: str, bbox: tuple) -> None:
    data = _load()
    data.setdefault(str(chat_id), {})[name] = list(bbox)
    _save(data)


def remove_user_region(chat_id: int, name: str) -> bool:
    data = _load()
    regions = data.get(str(chat_id), {})
    if name not in regions:
        return False
    del regions[name]
    _save(data)
    return True
