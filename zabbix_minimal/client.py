from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from zabbix_minimal.models import Problem, Host, Interface
from typing import List, Dict, Any, Optional
import logging
import time

logger = logging.getLogger(__name__)


class HostCache:
    def __init__(self, ttl_seconds: int = 300):
        self.cache = {}
        self.last_refresh = time.time()
        self.ttl_seconds = ttl_seconds

    def is_expired(self) -> bool:
        return time.time() - self.last_refresh > self.ttl_seconds

    def refresh(self):
        self.cache.clear()
        self.last_refresh = time.time()

    def get_missing(self, keys: List[str]) -> List[str]:
        if self.is_expired():
            self.refresh()
        return [k for k in keys if k not in self.cache]

    def update(self, new_data: Dict[str, Any]):
        self.cache.update(new_data)

    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        if self.is_expired():
            self.refresh()
        return {k: self.cache[k] for k in keys if k in self.cache}


class ZabbixClint:
    def __init__(self, base_url: str, api_token: str, host_group_id: str = None, verify_lts: bool = True):

        if "://" in base_url and not base_url.startswith(("http://", "https://")):
            raise ValueError(f"Invalid URL scheme in {base_url}")
        if not base_url.startswith(("http://", "https://")):
            base_url = "http://" + base_url
        self.base_url = base_url.rstrip("/") + "/api_jsonrpc.php"
        self.token = api_token
        self.verify_lts = verify_lts

        if not host_group_id:
            self.host_group_id = []
        elif isinstance(host_group_id, list):
            self.host_group_id = [g for g in host_group_id if g]
        else:
            self.host_group_id = [host_group_id]

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

        # Initialize API caches
        self.event_host_cache = HostCache(ttl_seconds=300)
        self.host_ip_cache = HostCache(ttl_seconds=300)

    def test_zabbix_connection(self) -> dict:
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

    def get_current_problems(self) -> List[Problem]:
        raw_problems = self._call("problem.get", {
            "output": "extend",
            "suppressed": False,
            "recent": False,
            "sortfield": ["eventid"],
            "sortorder": "DESC",
            **({"groupids": self.host_group_id} if self.host_group_id else {}),
        })
        return [Problem.from_api(p) for p in raw_problems]

    def get_event_hosts(self, event_ids: List[str]) -> Dict[str, List[Host]]:
        if not event_ids:
            return {}

        missing_event_ids = self.event_host_cache.get_missing(event_ids)

        if missing_event_ids:
            raw_hosts = self._call("event.get", {
                "eventids": missing_event_ids,
                "output": ["eventid"],
                "selectHosts": ["hostid", "name", "status"]
            })

            new_event_host_map = {}
            for event in raw_hosts:
                event_id = str(event["eventid"])
                hosts = [Host.from_api(h) for h in event.get("hosts", [])]
                new_event_host_map[event_id] = hosts

            self.event_host_cache.update(new_event_host_map)

        return self.event_host_cache.get_many(event_ids)

    def get_host_ips(self, host_ids: List[str]) -> Dict[str, str]:
        if not host_ids:
            return {}

        missing_host_ids = self.host_ip_cache.get_missing(host_ids)

        if missing_host_ids:
            raw_hosts = self._call("host.get", {
                "hostids": missing_host_ids,
                "output": ["hostid"],
                "selectInterfaces": ["ip", "main"]
            })

            new_ip_map = {}

            for host_data in raw_hosts:
                host_id = str(host_data["hostid"])
                interfaces_data = host_data.get("interfaces", [])

                # Convert raw interface data to Interface models
                interfaces = [Interface.from_api(iface)
                              for iface in interfaces_data]

                ip = "N/A"

                for interface in interfaces:
                    if interface.main:
                        ip = interface.ip
                        break

                if ip == "N/A" and interfaces:
                    ip = interfaces[0].ip

                new_ip_map[host_id] = ip

            self.host_ip_cache.update(new_ip_map)

        return self.host_ip_cache.get_many(host_ids)

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
