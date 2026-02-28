from unittest.mock import patch, MagicMock
import pytest

from zabbix_minimal.client import ZabbixClint
from zabbix_minimal.models import Problem


"""URL Validation Test"""


def test_zabbix_client_invalid_url():
    with pytest.raises(ValueError):
        ZabbixClint("ftp://invalid-url.com", "token", ["22"])


"""get_current_problems returns Problem objects"""


def test_get_current_problems():
    client = ZabbixClint("http://example.com", "token", ["22"])

    fake_problem = [{
        "eventid": "1",
        "name": "CPU High",
        "severity": "3",
        "acknowledged": "0",
        "clock": "1234567890",
        "hosts": [{
            "hostid": "1",
            "name": "Server1",
            "status": "0"
        }]
    }]

    fake_event_hosts = [{
        "eventid": "1",
        "hosts": [{
            "hostid": "1",
            "name": "Server1",
            "status": "0"
        }]
    }]

    with patch.object(client, "_call") as mock_call:
        mock_call.side_effect = [fake_problem, fake_event_hosts]

        problems = client.get_current_problems()

        assert len(problems) == 1
        assert isinstance(problems[0], Problem)
        assert problems[0].name == "CPU High"
        assert problems[0].primary_host.name == "Server1"


"""is_connected Success"""


def test_is_connected_success():
    client = ZabbixClint("http://10.10.10.10", "token", ["22"])

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": "6.0.0"}
    mock_response.raise_for_status.return_value = None

    with patch.object(client.session, "post", return_value=mock_response):
        assert client.is_connected() is True


"""is_connected Failure"""


def test_is_connected_failure():
    client = ZabbixClint("http://10.10.10.10", "token", ["22"])

    with patch.object(client.session, "post", side_effect=Exception("Connection error")):
        assert client.is_connected() is False
