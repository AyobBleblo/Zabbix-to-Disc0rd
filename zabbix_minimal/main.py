from .api import ZabbixClint
from .config import ZABBIX_URL, ZABBIX_TOKEN
from .monitor import ZabbixMonitor
from datetime import datetime
from .logging_config import setup_logging
import logging

setup_logging(logging.INFO)

logger = logging.getLogger(__name__)


def format_time(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def main():

    if not ZABBIX_URL or not ZABBIX_TOKEN:
        raise ValueError("ZABBIX_URL or ZABBIX_TOKEN is not set")

    client = ZabbixClint(ZABBIX_URL, ZABBIX_TOKEN, host_group_id="22")

    if not client.is_connected():
        logger.error("Zabbix server is not reachable")
        return

    logger.info("Connected to Zabbix")

    problems = client.get_current_problems()  # Returns List[Problem]
    if not problems:
        logger.info("No problems found")
        return

    # Use dot-notation because problems are now Problem dataclass objects
    event_ids = [problem.eventid for problem in problems]
    event_host_map_raw = client.get_event_hosts(event_ids)
    logger.info(f"{len(problems)} problems found")

    event_host_map = {}
    host_ids = []

    for event_id, hosts in event_host_map_raw.items():
        if hosts:
            host = hosts[0]
            event_host_map[event_id] = host
            host_ids.append(host.hostid)

    ip_map = client.get_host_ips(host_ids)

    for problem in problems:
        host = event_host_map.get(problem.eventid)
        if not host:
            continue

        if problem.severity == 1:
            ip = ip_map.get(host.hostid, "N/A")
            logger.info(
                f"Problem: {problem.name} | Host: {host.name} | IP: {ip} | Resolved: {problem.is_resolved}")


def print_problems_callback(current, new, resolved):
    logger.info("="*50)
    logger.info(
        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Zabbix Monitor Update")
    logger.info("="*50)

    if new:
        logger.warning(f"[!] NEW PROBLEMS ({len(new)}):")
        for p in new:
            logger.warning(
                f"  - [Severity: {p.severity}] {p.name} (Event ID: {p.eventid})")

    if resolved:
        logger.info(f"[v] RESOLVED PROBLEMS ({len(resolved)}):")
        for p in resolved:
            logger.info(
                f"  - [Severity: {p.severity}] {p.name} (Event ID: {p.eventid})")

    if not new and not resolved:
        logger.info(
            f"No changes. Currently tracking {len(current)} active problems.")

    logger.info("="*50)


if __name__ == "__main__":

    client = ZabbixClint(ZABBIX_URL, ZABBIX_TOKEN, host_group_id=["22"])
    monitor = ZabbixMonitor(client)
    client.test_zabbix_connection()

    logger.info("Starting Zabbix Monitor polling every 10 seconds...")
    try:
        monitor.start_polling(10, print_problems_callback, on_change_only=True)
    except KeyboardInterrupt:
        logger.info("Stopping monitor...")
        monitor.stop()
