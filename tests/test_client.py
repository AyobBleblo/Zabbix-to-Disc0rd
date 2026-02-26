from unittest.mock import patch
import pytest
from zabbix_minimal.client import ZabbixClint
from zabbix_minimal.config import ZABBIX_URL, ZABBIX_TOKEN


def test_zabbix_client_url():
    with pytest.raises(ValueError):
        ZabbixClint("ftp://invalid-url.com", ZABBIX_TOKEN)


def test_get_current_problems():
    client = ZabbixClint(ZABBIX_URL, ZABBIX_TOKEN)

    fake_response = [{
        "eventid": "1",
        "name": "CPU High",
        "severity": "3",
        "clock": "1234567890",
    }]

    with patch.object(client, "_call", return_value=fake_response):
        problems = client.get_current_problems()
        assert len(problems)
        assert problems[0].name == "CPU High"


def test_is_connected_success():
    client = ZabbixClint("http://10.10.10.10", ZABBIX_TOKEN)
    with patch.object(client.session, "post")as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"result": "6.0.0"}
        assert client.is_connected() is True

        print(mock_post.return_value.status_code)
