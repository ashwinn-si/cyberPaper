import json
import os
from datetime import datetime


def get_cache_path(cache_name: str = "eval_cache") -> str:
    """Get cache file path."""
    return f"results/{cache_name}.json"


def load_cache(cache_name: str = "eval_cache") -> dict:
    """Load cache file. Returns {} if not exist."""
    path = get_cache_path(cache_name)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_cache(cache_data: dict, cache_name: str = "eval_cache") -> None:
    """Save cache to file."""
    os.makedirs("results", exist_ok=True)
    path = get_cache_path(cache_name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, indent=2)


def add_to_cache(cache_data: dict, item_id, result: dict, cache_name: str = "eval_cache") -> dict:
    """Add result to cache and save."""
    if "items" not in cache_data:
        cache_data["items"] = {}
        cache_data["last_updated"] = datetime.now().isoformat()

    cache_data["items"][str(item_id)] = result
    cache_data["last_updated"] = datetime.now().isoformat()
    save_cache(cache_data, cache_name)
    return cache_data


def get_cached_result(cache_data: dict, item_id) -> dict | None:
    """Get result from cache by item_id. Returns None if not found."""
    if cache_data and "items" in cache_data:
        return cache_data["items"].get(str(item_id))
    return None


def get_cached_ids(cache_data: dict) -> set:
    """Get set of item IDs already cached."""
    if cache_data and "items" in cache_data:
        return set(cache_data["items"].keys())
    return set()


def validate_cache(cache_name: str = "eval_cache") -> bool:
    """
    Validate cache file is valid JSON.
    If corrupted, delete it and return False.
    Returns True if valid or doesn't exist.
    """
    path = get_cache_path(cache_name)
    if not os.path.exists(path):
        return True  # OK, doesn't exist yet

    try:
        with open(path, "r", encoding="utf-8") as f:
            json.load(f)
        return True  # Valid JSON
    except (json.JSONDecodeError, IOError) as e:
        print(f"⚠️  [Cache] {cache_name} corrupted: {e}")
        os.remove(path)
        print(f"   Deleted {path}. Restart will begin from item 1.")
        return False
