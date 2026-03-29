import json
import logging
from typing import List, Set
from ..models import Problem

logger = logging.getLogger(__name__)


class ProblemFilter:
    """
    Decides whether a problem should be forwarded to Discord.

    Config dict example:
    {
        "min_severity": 3,
        "include_substrings": ["device_offline", "link_down"],
        "exclude_substrings": ["power"],
        "host_ignores": [
            {"substring": "lowcablespeedlink1", "hostname": "1SW"}
        ]
    }
    """

    def __init__(self, config: dict):
        # Parse allowed_severities — accepts JSON string, list, or legacy int
        raw = config.get("allowed_severities") or config.get("min_severity", list(range(6)))
        if isinstance(raw, str):
            raw = json.loads(raw) if raw.strip() else list(range(6))
        if isinstance(raw, int):
            # Backward compat: old min_severity int → everything at or above it
            raw = list(range(raw, 6))
        self.allowed_severities: Set[int] = set(int(s) for s in raw)

        # Parse include substrings (might be JSON string from DB or a list)
        raw_include = config.get("include_substrings", [])
        if isinstance(raw_include, str):
            raw_include = json.loads(raw_include) if raw_include else []
        self.include_substrings = [s.strip().lower()
                                   for s in raw_include if s.strip()]

        # Parse exclude substrings
        raw_exclude = config.get("exclude_substrings", [])
        if isinstance(raw_exclude, str):
            raw_exclude = json.loads(raw_exclude) if raw_exclude else []
        self.exclude_substrings = [s.strip().lower()
                                   for s in raw_exclude if s.strip()]

        # Parse host-specific ignore rules
        raw_ignores = config.get("host_ignores", [])
        if isinstance(raw_ignores, str):
            raw_ignores = json.loads(raw_ignores) if raw_ignores else []
        self.host_ignores = raw_ignores

    def should_send(self, problem: Problem) -> bool:
        """Returns True if the problem should be sent to Discord."""
        name_lower = problem.name.lower()

        # Rule 1: Severity must be in the chosen set
        if problem.severity not in self.allowed_severities:
            return False

        # Rule 2: Must match at least one include substring (if configured)
        if self.include_substrings:
            if not any(sub in name_lower for sub in self.include_substrings):
                return False

        # Rule 3: Must NOT match any exclude substring
        if any(sub in name_lower for sub in self.exclude_substrings):
            return False

        # Rule 4: Check host-specific ignore rules
        host_names = [h.name.lower()
                      for h in problem.hosts] if problem.hosts else []
        for rule in self.host_ignores:
            sub = rule.get("substring", "").lower()
            host = rule.get("hostname", "").lower()
            if sub and host and sub in name_lower:
                if any(host in h for h in host_names):
                    return False

        return True
