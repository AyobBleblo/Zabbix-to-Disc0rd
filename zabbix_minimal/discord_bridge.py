import sqlite3
import logging
from collections import defaultdict
from typing import Dict, List, Tuple

from .discord.sender import DiscordBot
from .discord.filters import ProblemFilter
from .models import Problem

logger = logging.getLogger(__name__)


class DiscordBridge:
    """
    On every poll cycle:
    1. Receive all active problems (already enriched with host/IP metadata)
    2. For each enabled channel: filter → group by severity → delete old → send fresh
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._bots: Dict[str, DiscordBot] = {}

    # ── DB helpers ──────────────────────────────────────────────────────────────

    def _get_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def load_channels(self) -> List[dict]:
        conn = self._get_db()
        rows = conn.execute("SELECT * FROM channels WHERE enabled = 1").fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def _get_bot(self, token: str) -> DiscordBot:
        if token not in self._bots:
            self._bots[token] = DiscordBot(token)
        return self._bots[token]

    # ── Tracking helpers ────────────────────────────────────────────────────────

    def _get_tracked_messages(self, channel_config_id: int, severity: int) -> List[int]:
        """Return Discord message IDs currently tracked for this (channel, severity)."""
        conn = self._get_db()
        rows = conn.execute(
            "SELECT discord_message_id FROM message_tracking "
            "WHERE channel_config_id = ? AND severity = ? ORDER BY id",
            (channel_config_id, severity),
        ).fetchall()
        conn.close()
        return [int(r["discord_message_id"]) for r in rows]

    def _clear_tracking(self, channel_config_id: int, severity: int):
        conn = self._get_db()
        conn.execute(
            "DELETE FROM message_tracking WHERE channel_config_id = ? AND severity = ?",
            (channel_config_id, severity),
        )
        conn.commit()
        conn.close()

    def _save_tracking(self, channel_config_id: int, severity: int, message_ids: List[int]):
        conn = self._get_db()
        for msg_id in message_ids:
            conn.execute(
                "INSERT INTO message_tracking (channel_config_id, severity, discord_message_id) "
                "VALUES (?, ?, ?)",
                (channel_config_id, severity, str(msg_id)),
            )
        conn.commit()
        conn.close()

    # ── Main entry point ────────────────────────────────────────────────────────

    async def refresh_channel(
        self,
        channel_config: dict,
        problems_with_meta: List[Tuple[Problem, str, str]],  # (problem, host_name, ip)
    ):
        """
        Refresh all batch messages for one channel config.

        problems_with_meta should be the FULL list of currently active problems,
        each paired with (hostname, ip).
        """
        filter_config = {
            "allowed_severities": channel_config["allowed_severities"],
            "include_substrings": channel_config["include_substrings"],
            "exclude_substrings": channel_config["exclude_substrings"],
            "host_ignores": channel_config["host_ignores"],
        }
        problem_filter = ProblemFilter(filter_config)
        bot = self._get_bot(channel_config["bot_token"])
        channel_id = channel_config["discord_channel_id"]
        config_id = channel_config["id"]

        import json
        raw_sevs = channel_config["allowed_severities"]
        if isinstance(raw_sevs, str):
            allowed_sevs = set(json.loads(raw_sevs))
        else:
            allowed_sevs = set(raw_sevs)

        # 1. Filter and keep only matching problems (with their meta)
        filtered = [
            (p, host, ip)
            for p, host, ip in problems_with_meta
            if problem_filter.should_send(p)
        ]

        # 2. Group by severity
        by_severity: Dict[int, List[Tuple[Problem, str, str]]] = defaultdict(list)
        for p, host, ip in filtered:
            by_severity[p.severity].append((p, host, ip))

        # 3. For each chosen severity: delete old → send new
        for sev in sorted(allowed_sevs):
            group = by_severity.get(sev, [])

            # a. Delete old Discord messages
            old_ids = self._get_tracked_messages(config_id, sev)
            if old_ids:
                await bot.delete_messages(int(channel_id), old_ids)

            # b. Clear old tracking rows
            self._clear_tracking(config_id, sev)

            # c. Send new batch (only when there are problems at this severity)
            if group:
                new_ids = await bot.send_batch(channel_id, group, sev)
                self._save_tracking(config_id, sev, new_ids)
                logger.info(
                    f"[{channel_config['name']}] sev={sev}: "
                    f"{len(group)} problems → {len(new_ids)} message(s)"
                )

    async def process_all_channels(
        self,
        problems_with_meta: List[Tuple[Problem, str, str]],
    ):
        """Called every poll cycle. Refreshes every enabled channel."""
        channels = self.load_channels()
        for channel_config in channels:
            try:
                await self.refresh_channel(channel_config, problems_with_meta)
            except Exception:
                logger.exception(f"Error refreshing channel '{channel_config['name']}'")