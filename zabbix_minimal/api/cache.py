import time
from typing import List, Dict, Any


class HostCache:
    def __init__(self, ttl_seconds: int = 300):
        self.cache = {}
        self.last_refresh = time.time()
        self.ttl_seconds = ttl_seconds

    def is_expired(self) -> bool:
        return time.time() - self.last_refresh > self.ttl_seconds

    def refresh(self):
        self.cache.clear()
        self.last_refresh = time.time()

    def get_missing(self, keys: List[str]) -> List[str]:
        if self.is_expired():
            self.refresh()
        return [k for k in keys if k not in self.cache]

    def update(self, new_data: Dict[str, Any]):
        self.cache.update(new_data)

    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        if self.is_expired():
            self.refresh()
        return {k: self.cache[k] for k in keys if k in self.cache}
