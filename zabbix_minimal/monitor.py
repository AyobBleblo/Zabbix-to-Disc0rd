import time
import threading
from typing import List, Dict, Set, Tuple
from .models import Problem
from .client import ZabbixClint


class ZabbixMonitor:
    """
    Stateful monitoring service.
    Handles polling and change detection.
    """

    def __init__(self, client: ZabbixClint):
        self.client = client
        self._previous_problems: Dict[str, Problem] = {}
        self._lock = threading.Lock()
        self._running = False

    """
    Core Polling Logic
    """

    def poll_once(self) -> Tuple[List[Problem], List[Problem], List[Problem]]:
        """
        Performs a single poll cycle.
        Returns: (new_problems, resolved_problems, current_problems)
        """
        with self._lock:
            current_problems = self.client.get_current_problems()
            current_map = {p.eventid: p for p in current_problems}

            current_ids = set(current_map.keys())
            previous_ids = set(self._previous_problems.keys())

            new_ids = current_ids - previous_ids
            resolved_ids = previous_ids - current_ids

            new_problems = [current_map[eid] for eid in new_ids]
            resolved_problems = [self._previous_problems[eid]
                                 for eid in resolved_ids]

            # Update state
            self._previous_problems = current_map

            return new_problems, resolved_problems, current_problems

    def start_polling(self, interval: int, callback, on_change_only: bool = False):
        """
        interval: seconds
        callback: function(current, new, resolved)
        on_change_only: if True, only calls the callback when there are new or resolved problems.
        """
        self._running = True

        while self._running:
            try:
                # Fixed the unpacking order: poll_once returns (new, resolved, current)
                new, resolved, current = self.poll_once()

                if callback:
                    if not on_change_only or new or resolved:
                        callback(current, new, resolved)

            except Exception:
                # Let upper layers decide logging strategy
                pass

            time.sleep(interval)

    def stop(self):
        self._running = False
