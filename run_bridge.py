"""
Entry point: Zabbix Monitor → Discord Bridge
Polls Zabbix for problems, sends/deletes Discord messages.

Usage:
    python run_bridge.py
"""

import asyncio
import logging
import os
from typing import List, Tuple
from dotenv import load_dotenv

from zabbix_minimal.api import ZabbixClint
from zabbix_minimal.models import Problem
from zabbix_minimal.monitor import ZabbixMonitor
from zabbix_minimal.discord_bridge import DiscordBridge
from zabbix_minimal.logging_config import setup_logging

# Load environment
load_dotenv("zabbix_minimal/.env")
setup_logging(logging.INFO)
logger = logging.getLogger(__name__)

# Config
ZABBIX_URL = os.getenv("ZABBIX_URL")
ZABBIX_TOKEN = os.getenv("ZABBIX_TOKEN")
HOST_GROUP_ID = os.getenv("HOST_GROUP_ID", "22")
DB_PATH = os.getenv("DASHBOARD_DB_PATH", "dashboard.db")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "30"))  # seconds


def enrich_problems(
    problems: List[Problem],
    zabbix: ZabbixClint,
) -> List[Tuple[Problem, str, str]]:
    """
    Attach hostname and IP to each problem.
    Returns list of (problem, host_name, ip) tuples.
    """
    # 1. Fetch hosts for all event IDs in one batch call
    event_ids = [p.eventid for p in problems]
    event_host_map = zabbix.get_event_hosts(event_ids)  # {eventid: [Host]}

    # 2. Attach hosts to problems
    for problem in problems:
        if problem.eventid in event_host_map:
            problem.hosts = event_host_map[problem.eventid]

    # 3. Collect all unique host IDs
    all_host_ids = list({
        h.hostid
        for p in problems
        for h in p.hosts
    })

    # 4. Fetch IPs for all hosts in one batch call
    ip_map = zabbix.get_host_ips(all_host_ids)   # {hostid: "ip"}

    # 5. Build enriched list
    result = []
    for problem in problems:
        host = problem.primary_host
        host_name = host.name if host else "Unknown"
        ip = ip_map.get(host.hostid, "N/A") if host else "N/A"
        result.append((problem, host_name, ip))

    return result


async def main():
    if not ZABBIX_URL or not ZABBIX_TOKEN:
        logger.error("ZABBIX_URL or ZABBIX_TOKEN not set in .env")
        return

    # 1. Create Zabbix client
    client = ZabbixClint(ZABBIX_URL, ZABBIX_TOKEN, host_group_id=HOST_GROUP_ID)
    if not client.is_connected():
        logger.error("Cannot connect to Zabbix")
        return
    logger.info("Connected to Zabbix ✓")

    # 2. Create monitor and bridge
    monitor = ZabbixMonitor(client)
    bridge = DiscordBridge(DB_PATH)
    logger.info(f"Bridge ready, polling every {POLL_INTERVAL}s...")

    # 3. Poll loop
    while True:
        try:
            # We fetch exactly what is active right now
            _, _, current = monitor.poll_once()

            if current:
                logger.debug(f"{len(current)} active problems. Refreshing Discord batches...")
                problems_with_meta = enrich_problems(current, client)
                await bridge.process_all_channels(problems_with_meta)
            else:
                logger.debug("No active problems. Clearing any leftover Discord messages...")
                await bridge.process_all_channels([])

        except Exception:
            logger.exception("Error in poll cycle")

        await asyncio.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bridge stopped.")