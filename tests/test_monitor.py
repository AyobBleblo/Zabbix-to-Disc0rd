from unittest.mock import MagicMock, patch
import pytest

from zabbix_minimal.monitor import ZabbixMonitor
from zabbix_minimal.models import Problem


def test_monitor_poll_once_no_changes():
    mock_client = MagicMock()
    # first poll
    p1 = Problem(eventid="1", name="P1", severity=1,
                 acknowledged=False, clock=123)
    mock_client.get_current_problems.return_value = [p1]

    monitor = ZabbixMonitor(mock_client)
    new, resolved, current = monitor.poll_once()

    assert len(new) == 1
    assert len(resolved) == 0
    assert len(current) == 1
    assert new[0].eventid == "1"

    # second poll, no changes
    new, resolved, current = monitor.poll_once()
    assert len(new) == 0
    assert len(resolved) == 0
    assert len(current) == 1


def test_monitor_poll_once_resolved_and_new():
    mock_client = MagicMock()
    p1 = Problem(eventid="1", name="P1", severity=1,
                 acknowledged=False, clock=123)
    p2 = Problem(eventid="2", name="P2", severity=1,
                 acknowledged=False, clock=123)

    # Poll 1
    mock_client.get_current_problems.return_value = [p1]
    monitor = ZabbixMonitor(mock_client)
    monitor.poll_once()

    # Poll 2 (P1 removed, P2 added)
    mock_client.get_current_problems.return_value = [p2]
    new, resolved, current = monitor.poll_once()

    assert len(new) == 1
    assert new[0].eventid == "2"
    assert len(resolved) == 1
    assert resolved[0].eventid == "1"
    assert len(current) == 1
    assert current[0].eventid == "2"


def test_monitor_start_polling():
    mock_client = MagicMock()
    p1 = Problem(eventid="1", name="P1", severity=1,
                 acknowledged=False, clock=123)
    mock_client.get_current_problems.return_value = [p1]

    monitor = ZabbixMonitor(mock_client)

    cb_calls = []

    def my_callback(current, new, resolved):
        cb_calls.append((current, new, resolved))
        monitor.stop()  # stop after first iteration to avoid infinite loop

    with patch("time.sleep", return_value=None):
        monitor.start_polling(
            interval=10, callback=my_callback, on_change_only=False)

    assert len(cb_calls) == 1
    c, n, r = cb_calls[0]
    assert len(c) == 1
    assert len(n) == 1
