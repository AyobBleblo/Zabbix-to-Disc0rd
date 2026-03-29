import discord
import asyncio
import logging
from datetime import datetime
from typing import List, Tuple

from ..models import Problem

logger = logging.getLogger(__name__)

# ── Severity metadata ──────────────────────────────────────────────────────────
SEVERITY_MAP = {
    0: {"name": "Not classified", "emoji": "⬜", "color": 0x97AAB1},
    1: {"name": "Information",    "emoji": "🔵", "color": 0x7499FF},
    2: {"name": "Warning",        "emoji": "🟡", "color": 0xFFC859},
    3: {"name": "Average",        "emoji": "🟠", "color": 0xFFA059},
    4: {"name": "High",           "emoji": "🔴", "color": 0xFF3838},
    5: {"name": "Disaster",       "emoji": "💀", "color": 0xFF0000},
}

BATCH_SIZE = 20  # Max problems per embed (Discord allows 25 fields; 20 is safe)


def _build_batch_embed(
    problems_with_meta: List[Tuple[Problem, str, str]],   # (problem, host_name, ip)
    severity: int,
    chunk_index: int,
    total_chunks: int,
) -> discord.Embed:
    """
    Build one embed for a batch of problems at the same severity.

    problems_with_meta: list of (Problem, hostname, ip) tuples.
    """
    sev = SEVERITY_MAP.get(severity, SEVERITY_MAP[0])
    title = f"{sev['emoji']} {sev['name']} Problems"
    if total_chunks > 1:
        title += f"  ({chunk_index + 1}/{total_chunks})"

    embed = discord.Embed(
        title=title,
        color=sev["color"],
        timestamp=datetime.utcnow(),
    )

    for problem, host_name, ip in problems_with_meta:
        field_name = f"Host: {host_name}  |  IP: {ip}"
        field_value = f"`{problem.eventid}` {problem.name}"[:1024]
        embed.add_field(name=field_name[:256], value=field_value, inline=False)

    count = len(problems_with_meta)
    embed.set_footer(text=f"Zabbix Monitor • {count} problem(s)")
    return embed


class DiscordBot:
    """Sends batched problem messages in Discord and cleans up old ones."""

    def __init__(self, token: str):
        self.token = token
        self._client: discord.Client | None = None
        self._ready = asyncio.Event()

    # ── Connection ─────────────────────────────────────────────────────────────

    async def _ensure_client(self):
        if self._client and not self._client.is_closed():
            return

        intents = discord.Intents.default()
        self._client = discord.Client(intents=intents)

        @self._client.event
        async def on_ready():
            logger.info(f"Discord bot connected as {self._client.user}")
            self._ready.set()

        asyncio.create_task(self._client.start(self.token))
        await asyncio.wait_for(self._ready.wait(), timeout=30)

    async def _get_channel(self, channel_id: int):
        channel = self._client.get_channel(channel_id)
        if not channel:
            channel = await self._client.fetch_channel(channel_id)
        return channel

    # ── Public API ─────────────────────────────────────────────────────────────

    async def delete_messages(self, channel_id: int, message_ids: List[int]):
        """Delete a list of Discord messages (silently skip if already gone)."""
        await self._ensure_client()
        channel = await self._get_channel(channel_id)
        for msg_id in message_ids:
            try:
                msg = await channel.fetch_message(msg_id)
                await msg.delete()
                logger.debug(f"Deleted message {msg_id}")
            except discord.NotFound:
                pass
            except Exception:
                logger.exception(f"Could not delete message {msg_id}")

    async def send_batch(
        self,
        channel_id: int,
        problems_with_meta: List[Tuple[Problem, str, str]],  # (problem, host_name, ip)
        severity: int,
    ) -> List[int]:
        """
        Send problems as one or more embeds (chunks of BATCH_SIZE).
        Returns list of Discord message IDs that were sent.
        """
        if not problems_with_meta:
            return []

        await self._ensure_client()
        channel = await self._get_channel(int(channel_id))

        chunks = [
            problems_with_meta[i:i + BATCH_SIZE]
            for i in range(0, len(problems_with_meta), BATCH_SIZE)
        ]
        sent_ids: List[int] = []

        for idx, chunk in enumerate(chunks):
            embed = _build_batch_embed(chunk, severity, idx, len(chunks))
            try:
                msg = await channel.send(embed=embed)
                sent_ids.append(msg.id)
                logger.info(
                    f"Sent batch chunk {idx + 1}/{len(chunks)} "
                    f"sev={severity} ({len(chunk)} problems) → msg {msg.id}"
                )
            except Exception:
                logger.exception(f"Failed to send batch chunk {idx}")

        return sent_ids

    async def close(self):
        if self._client and not self._client.is_closed():
            await self._client.close()