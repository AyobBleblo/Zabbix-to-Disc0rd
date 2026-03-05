from typing import List, Dict, Any
from zabbix_minimal.models import Problem, Host, Interface
from .api_core import ZabbixApiCore


class ZabbixClint(ZabbixApiCore):

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
