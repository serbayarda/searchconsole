import time
import threading


class RateLimiter:
    def __init__(self, calls_per_minute: int):
        self._interval = 60.0 / calls_per_minute
        self._last_call = 0.0
        self._lock = threading.Lock()

    def wait(self) -> None:
        with self._lock:
            elapsed = time.time() - self._last_call
            if elapsed < self._interval:
                time.sleep(self._interval - elapsed)
            self._last_call = time.time()
