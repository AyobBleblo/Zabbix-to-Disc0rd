from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import List, Dict, Any
import logging
import time

logger = logging.getLogger(__name__)


class ZabbixClint:
    def __init__(self, base_url: str, api_token: str, host_group_id: str = None, verify_lts: bool = True):

        if not base_url.startswith("http://"):
            raise ValueError("base_url must start with http:// or https://")
        self.base_url = base_url.rstrip("/") + "/api_jsonrpc.php"
        self.token = api_token
        self.verify_lts = verify_lts
        self.host_group_id = host_group_id or []
        self.session = Session()
        self.session.headers.update({
            "Content-Type": "application/json",
        })
        retries = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def test_zabbix_connection (self) -> dict:
        result = {
            "connection": False,
            "problems_fetch": False,
            "error": None
        }
        print("____________________________________________________________")
        print("Test zabbix connection result:")
        print("____________________________________________________________")
        try:
            if not self.is_connected():
                result["connection"] = "Connection failed"
                return result

            result["connection"] = True

            problems = self.get_current_problems()
            result["problems_fetch"] = isinstance(problems, list)

        except Exception as e:
            result["error"] = str(e)

        print(
            f"Connections state: {result.get('connection')} , Problems fetch state: {result.get('problems_fetch')} , Error: {result.get('error')}")
        print("____________________________________________________________")

    def _call(self, method: str, params: Dict[str, Any] | None = None) -> Any:
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "auth": self.token,
            "id": 1,
        }

        try:
            start = time.time()

            logger.debug(f"Calling Zabbix API method: {method}")

            # Note: The original identifier was verify_lts in __init__
            response = self.session.post(
                self.base_url,
                json=payload,
                verify=self.verify_lts,
                timeout=40,
            )

            response.raise_for_status()
            data = response.json()

            duration = time.time() - start

            if "error" in data:
                logger.error(
                    f"Zabbix API returned error for {method}: {data['error']}")
                raise RuntimeError(data["error"])

            logger.info(f"{method} succeeded in {duration:.2f}s")

            return data["result"]

        except Exception:
            logger.exception(f"API call failed for method: {method}")
            raise

    def get_current_problems(self) -> List[Dict[str, Any]]:

        params = {
            "output": ["name", "severity", "clock", "eventid"],
            "recent": False,
            "sortfield": "eventid",
            "sortorder": "DESC",
        }
        if self.host_group_id:
            params["groupids"] = self.host_group_id
        return self._call("problem.get", params)

    def get_event_hosts(self, event_ids) -> List[Dict[str, Any]]:
        return self._call("event.get", {
            "eventids": event_ids,
            "output": ["eventid"],
            "selectHosts": ["hostid", "name"]
        })

    def get_host_ips(self, host_ids):
        hosts = self._call("host.get", {
            "hostids": host_ids,
            "output": ["hostid"],
            "selectInterfaces": ["ip", "main"]
        })

        ip_map = {}

        for host in hosts:
            interfaces = host.get("interfaces", [])

            ip = "N/A"

            for interface in interfaces:
                if interface.get("main") == "1":
                    ip = interface.get("ip")
                    break

            if ip == "N/A" and interfaces:
                ip = interfaces[0].get("ip", "N/A")

            ip_map[host["hostid"]] = ip

        return ip_map

    def is_connected(self) -> bool:
        try:
            logger.debug("Checking Zabbix API health")

            payload = {
                "jsonrpc": "2.0",
                "method": "apiinfo.version",
                "params": [],
                "id": 1
            }

            response = self.session.post(
                self.base_url,
                json=payload,
                verify=self.verify_lts,
                timeout=5
            )

            response.raise_for_status()
            data = response.json()

            logger.info("Zabbix connection successful")
            return "result" in data

        except Exception:
            logger.warning("Zabbix connection failed")
            return False
