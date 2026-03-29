import pytest
from zabbix_minimal.discord.sender import _build_batch_embed, BATCH_SIZE
from zabbix_minimal.models import Problem, Host


def make_problem(eventid, name, severity):
    host = Host(hostid="h1", name="Router-01", status=0)
    return Problem(
        eventid=str(eventid), name=name, severity=severity,
        acknowledged=False, clock=1000, hosts=[host],
    )


def meta(problem, host="Router-01", ip="10.0.0.1"):
    return (problem, host, ip)


def test_embed_has_host_and_ip():
    p = make_problem(1, "Link down", 4)
    embed = _build_batch_embed([meta(p)], severity=4, chunk_index=0, total_chunks=1)
    field = embed.fields[0]
    assert "Router-01" in field.name
    assert "10.0.0.1" in field.name


def test_embed_field_count():
    problems = [meta(make_problem(i, f"Problem {i}", 3)) for i in range(15)]
    embed = _build_batch_embed(problems, severity=3, chunk_index=0, total_chunks=1)
    assert len(embed.fields) == 15


def test_chunk_counter_in_title():
    problems = [meta(make_problem(i, f"P{i}", 2)) for i in range(3)]
    embed = _build_batch_embed(problems, severity=2, chunk_index=1, total_chunks=3)
    assert "2/3" in embed.title


def test_no_chunk_counter_for_single_chunk():
    problems = [meta(make_problem(1, "Disk full", 5))]
    embed = _build_batch_embed(problems, severity=5, chunk_index=0, total_chunks=1)
    assert "1/1" not in embed.title