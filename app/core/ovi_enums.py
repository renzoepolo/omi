import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def get_ovi_enum_definitions() -> dict[str, list[dict[str, int | str]]]:
    file_path = Path(__file__).resolve().parents[2] / "shared" / "ovi_enums.json"
    with file_path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    return payload


@lru_cache(maxsize=1)
def get_ovi_allowed_codes() -> dict[str, set[int]]:
    return {
        key: {int(item["code"]) for item in values}
        for key, values in get_ovi_enum_definitions().items()
    }
