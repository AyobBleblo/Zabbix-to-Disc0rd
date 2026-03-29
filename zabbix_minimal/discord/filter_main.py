from zabbix_minimal.models import Problem, Host
from zabbix_minimal.discord.filters import ProblemFilter


# Create a filter: only severity 3+, ignore "power" problems
config = {
    "min_severity": 3,
    "exclude_substrings": ["power"],
    "host_ignores": [{"substring": "lowcablespeedlink1", "hostname": "1SW"}]
}
f = ProblemFilter(config)

# Test 1: High severity problem → should PASS
p1 = Problem(eventid="1", name="Interface eth0 down", severity=4,
             acknowledged=False, clock=1000)
print(f.should_send(p1))  # True ✅

# Test 2: Low severity → should FAIL
p2 = Problem(eventid="2", name="Some info", severity=1,
             acknowledged=False, clock=1000)
print(f.should_send(p2))  # False ❌

# Test 3: Contains "power" → should FAIL
p3 = Problem(eventid="3", name="Power supply failure", severity=5,
             acknowledged=False, clock=1000)
print(f.should_send(p3))  # False ❌

# Test 4: Host-specific ignore → should FAIL
host = Host(hostid="10", name="1SW", status=0)
p4 = Problem(eventid="4", name="lowcablespeedlink1 detected", severity=4,
             acknowledged=False, clock=1000, hosts=[host])
print(f.should_send(p4))  # False ❌
