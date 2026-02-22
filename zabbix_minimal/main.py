from client import ZabbixClint
from config import ZABBIX_URL, ZABBIX_TOKEN
from datetime import datetime
from logging_config import setup_logging
import logging

setup_logging(logging.INFO)

logger = logging.getLogger(__name__)

def format_time(timestamp: str) -> str:
    return datetime.fromtimestamp(int(timestamp)).strftime("%Y-%m-%d %H:%M:%S")

"""j"""
def main():

    if not ZABBIX_URL or not ZABBIX_TOKEN:
        raise ValueError("ZABBIX_URL or ZABBIX_TOKEN is not set")

    client = ZabbixClint(ZABBIX_URL, ZABBIX_TOKEN, host_group_id="22")

    if not client.is_connected():
        print("Zabbix server is not reachable")
        return

    logger.info("Connected to Zabbix")

    problems = client.get_current_problems()
    if not problems:
        logger.info("No problems found")
        return

    event_ids = [problem["eventid"] for problem in problems]
    # print(problems[0])
    # print(event_ids[0])
    events = client.get_event_hosts(event_ids)
    print(f"{len(problems)} problems found")
    # print(events[0])

    event_host_map = {}

    host_ids = []
    for event in events:
        hosts = event.get("hosts")

        if hosts:
            host = hosts[0]
            event_host_map[event["eventid"]] = host
            host_ids.append(host["hostid"])

    ip_map = client.get_host_ips(host_ids)

    for problem in problems:
        event_id = problem["eventid"]
        host_info = event_host_map.get(event_id)
        if not host_info:
            continue

        if problem["severity"] == "1":
            host_name = host_info["name"]
            host_id = host_info["hostid"]
            ip = ip_map.get(host_id, "N/A")

            # print(
            #     f"{problem['name']} ({problem['severity']}) - {ip}     {host_name}")


if __name__ == "__main__":

    client = ZabbixClint(ZABBIX_URL, ZABBIX_TOKEN, host_group_id=["22"])
    client.test_zabbix_connection()
    main()
