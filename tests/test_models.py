import pytest

from zabbix_minimal.models import Host, Interface, Problem


def test_host_is_enabled():
    h1 = Host(hostid="1", name="H1", status=0)
    assert h1.is_enabled is True

    h2 = Host(hostid="2", name="H2", status=1)
    assert h2.is_enabled is False


def test_interface_from_api_main():
    data = {"ip": "1.2.3.4", "main": "1"}
    interface = Interface.from_api(data)
    assert interface.ip == "1.2.3.4"
    assert interface.main is True


def test_problem_is_resolved():
    p1 = Problem(eventid="1", name="P1", severity=1,
                 acknowledged=False, clock=123)
    assert p1.is_resolved is False  # r_eventid is None

    p2 = Problem(eventid="2", name="P2", severity=1,
                 acknowledged=False, clock=123, r_eventid="0")
    assert p2.is_resolved is False  # r_eventid is "0"

    p3 = Problem(eventid="3", name="P3", severity=1,
                 acknowledged=False, clock=123, r_eventid="456")
    assert p3.is_resolved is True   # r_eventid is not "0"


def test_problem_host_ids():
    h1 = Host(hostid="101", name="H1", status=0)
    h2 = Host(hostid="102", name="H2", status=0)
    p = Problem(eventid="1", name="P1", severity=1,
                acknowledged=False, clock=123, hosts=[h1, h2])
    assert p.host_ids == ["101", "102"]
