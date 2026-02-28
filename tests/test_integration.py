import pytest
from zabbix_minimal.client import ZabbixClint
from zabbix_minimal.monitor import ZabbixMonitor
from zabbix_minimal.config import ZABBIX_URL, ZABBIX_TOKEN, HOST_GROUP_ID


pytestmark = pytest.mark.integration


def test_real_api_connection():
    url = ZABBIX_URL
    token = ZABBIX_TOKEN
    group = HOST_GROUP_ID

    client = ZabbixClint(url, token, [group])

    assert client.is_connected() is True


def test_real_problem_fetch():
    url = ZABBIX_URL
    token = ZABBIX_TOKEN
    group = HOST_GROUP_ID

    client = ZabbixClint(url, token, [group])

    problems = client.get_current_problems()

    assert isinstance(problems, list)

    if problems:
        p = problems[0]
        assert hasattr(p, "eventid")
        assert hasattr(p, "severity")


def test_monitor_integration():
    url = ZABBIX_URL
    token = ZABBIX_TOKEN
    group = HOST_GROUP_ID

    client = ZabbixClint(url, token, [group])
    monitor = ZabbixMonitor(client)

    current, new, resolved = monitor.poll_once()

    assert isinstance(current, list)
    assert isinstance(new, list)
    assert isinstance(resolved, list)
