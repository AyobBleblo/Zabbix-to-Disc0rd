from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


"""Host Model"""


@dataclass
class Host:
    hostid: str
    name: str
    status: int  # 0 = enabled, 1 = disabled

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "Host":
        return cls(
            hostid=str(data.get("hostid")),
            name=data.get("name", "Unknown"),
            status=int(data.get("status", 1)),
        )

    @property
    def is_enabled(self) -> bool:
        return self.status == 0


"""Interface Model"""


@dataclass
class Interface:
    ip: str
    main: bool

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "Interface":
        return cls(
            ip=data.get("ip", "N/A"),
            main=data.get("main") == "1",
        )


"""Problem Model"""

@dataclass
class Problem:
    eventid: str
    name: str
    severity: int
    acknowledged: bool
    clock: int
    opdata: Optional[str] = None
    hosts: List[Host] = field(default_factory=list)
    r_eventid: Optional[str] = None
    r_clock: Optional[int] = None

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "Problem":
        hosts_data = data.get("hosts", [])
        hosts = [Host.from_api(h) for h in hosts_data]

        return cls(
            eventid=str(data.get("eventid")),
            name=data.get("name", "Unknown"),
            severity=int(data.get("severity", 0)),
            acknowledged=bool(data.get("acknowledged", False)),
            clock=int(data.get("clock", 0)),
            opdata=data.get("opdata"),
            hosts=hosts,
            r_eventid=data.get("r_eventid"),
            r_clock=int(data["r_clock"]) if data.get("r_clock") else None,
        )

    @property
    def is_resolved(self) -> bool:
        return bool(self.r_eventid and self.r_eventid != "0")

    @property
    def host_ids(self) -> List[str]:
        return [h.hostid for h in self.hosts]

    @property
    def primary_host(self) -> Optional[Host]:
        return self.hosts[0] if self.hosts else None
