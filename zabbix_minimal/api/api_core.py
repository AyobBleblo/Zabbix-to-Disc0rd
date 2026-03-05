from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, Any, List
from .cache import HostCache
import logging
import time

logger = logging.getLogger(__name__)


class ZabbixApiCore:
    def __init__(self, base_url: str, api_token: str, host_group_id: str | List[str] = None, verify_lts: bool = True):

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

            # This method will be implemented by the child class (ZabbixClint)
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

    def get_current_problems(self) -> List[Any]:
        return []
