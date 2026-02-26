from client import ZabbixClint
from config import ZABBIX_URL, ZABBIX_TOKEN
from datetime import datetime
from logging_config import setup_logging
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
        print("Zabbix server is not reachable")
        return

    logger.info("Connected to Zabbix")

    problems = client.get_current_problems()  # Returns List[Problem]
    if not problems:
        logger.info("No problems found")
        return

    # Use dot-notation because problems are now Problem dataclass objects
    event_ids = [problem.eventid for problem in problems]
    event_host_map_raw = client.get_event_hosts(event_ids)
    print(f"{len(problems)} problems found")

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
            print(f"{problem.name} (severity={problem.severity}) - {ip}  {host.name}")
            logger.info(
                f"Problem: {problem.name} | Host: {host.name} | IP: {ip} | Resolved: {problem.is_resolved}")


if __name__ == "__main__":

    client = ZabbixClint(ZABBIX_URL, ZABBIX_TOKEN, host_group_id=["22"])
    client.test_zabbix_connection()
    main()
