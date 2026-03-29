import pytest
from zabbix_minimal.discord.filters import ProblemFilter
from zabbix_minimal.models import Problem, Host

def make_problem(name, severity):
    host = Host(hostid="h1", name="Router-01", status=0)
    return Problem(
        eventid="123", name=name, severity=severity,
        acknowledged=False, clock=1000, hosts=[host]
    )

def test_allowed_severities_exact_match():
    f = ProblemFilter({"allowed_severities": [1, 2]})
    assert f.should_send(make_problem("Info event", severity=1)) is True
    assert f.should_send(make_problem("Warning event", severity=2)) is True
    assert f.should_send(make_problem("Average event", severity=3)) is False
    assert f.should_send(make_problem("High event", severity=4)) is False

def test_allowed_severities_single_level():
    f = ProblemFilter({"allowed_severities": [4]})
    assert f.should_send(make_problem("High event", severity=4)) is True
    assert f.should_send(make_problem("Disaster event", severity=5)) is False
    assert f.should_send(make_problem("Warning event", severity=2)) is False

def test_allowed_severities_from_json_string():
    """The DB sends a JSON string — make sure the filter parses it correctly."""
    f = ProblemFilter({"allowed_severities": "[2,4]"})
    assert f.should_send(make_problem("Warning", severity=2)) is True
    assert f.should_send(make_problem("High", severity=4)) is True
    assert f.should_send(make_problem("Info", severity=1)) is False