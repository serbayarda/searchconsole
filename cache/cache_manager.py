from __future__ import annotations
import json
import hashlib
import os
import time
from functools import wraps


class CacheManager:
    def __init__(self, cache_dir: str, ttl_seconds: int = 3600):
        self._cache_dir = cache_dir
        self._ttl = ttl_seconds
        os.makedirs(cache_dir, exist_ok=True)

    def _path(self, key: str) -> str:
        return os.path.join(self._cache_dir, f"{key}.json")

    def get(self, key: str) -> dict | list | None:
        path = self._path(key)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r") as f:
                data = json.load(f)
            if time.time() - data.get("_ts", 0) > self._ttl:
                os.remove(path)
                return None
            return data.get("value")
        except (json.JSONDecodeError, KeyError):
            return None

    def set(self, key: str, value) -> None:
        path = self._path(key)
        with open(path, "w") as f:
            json.dump({"_ts": time.time(), "value": value}, f, default=str)

    def make_key(self, *args) -> str:
        raw = json.dumps(args, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()

    def cached(self, prefix: str):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                key = f"{prefix}_{self.make_key(args[1:], kwargs)}"
                cached_val = self.get(key)
                if cached_val is not None:
                    return cached_val
                result = func(*args, **kwargs)
                if result is not None:
                    self.set(key, result)
                return result
            return wrapper
        return decorator

    def clear_all(self) -> int:
        count = 0
        for f in os.listdir(self._cache_dir):
            if f.endswith(".json"):
                os.remove(os.path.join(self._cache_dir, f))
                count += 1
        return count

    def clear_expired(self) -> int:
        count = 0
        for f in os.listdir(self._cache_dir):
            if not f.endswith(".json"):
                continue
            path = os.path.join(self._cache_dir, f)
            try:
                with open(path, "r") as fh:
                    data = json.load(fh)
                if time.time() - data.get("_ts", 0) > self._ttl:
                    os.remove(path)
                    count += 1
            except (json.JSONDecodeError, KeyError):
                os.remove(path)
                count += 1
        return count
