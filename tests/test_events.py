from pathlib import Path

import networkx as nx

from network_scene_generator.generators.events import generate_events
from network_scene_generator.rng import RandomManager
from network_scene_generator.writers.jsonl_writer import write_jsonl


class _Config:
    scene_duration = 10.0
    events = {
        "enabled": True,
        "event_probability": 0.0,
        "event_type_candidates": ["node_failure", "link_failure", "route_switch"],
        "failure_end_probability": 0.5,
        "route_switch": {"require_reachable_to_dst": True},
    }


def test_events_jsonl_empty_when_no_event(tmp_path: Path) -> None:
    graph = nx.Graph()
    graph.add_edge("A", "B")

    links = [{"link_id": "L0001", "src": "A", "dst": "B", "bandwidth_mbps": 100}]
    routing_map = {
        ("A", "A"): "A",
        ("A", "B"): "B",
        ("B", "A"): "A",
        ("B", "B"): "B",
    }

    rows = generate_events(graph, links, routing_map, _Config(), RandomManager(1))
    assert rows == []

    out = tmp_path / "events.jsonl"
    write_jsonl(out, rows)

    assert out.read_text(encoding="utf-8") == ""


class _NodeFailureNoEndConfig:
    scene_duration = 10.0
    events = {
        "enabled": True,
        "event_probability": 1.0,
        "event_type_candidates": ["node_failure"],
        "failure_end_probability": 0.0,
        "route_switch": {"require_reachable_to_dst": True},
    }


def test_node_failure_event_can_omit_end_time() -> None:
    graph = nx.Graph()
    graph.add_edge("A", "B")

    rows = generate_events(graph, [], {}, _NodeFailureNoEndConfig(), RandomManager(9))
    assert len(rows) == 1
    row = rows[0]

    assert row["event_type"] == "node_failure"
    assert row["target_type"] == "node"
    assert row["target_1"] in {"A", "B"}
    assert 0.0 <= row["event_time"] <= _NodeFailureNoEndConfig.scene_duration
    assert "end_time" not in row
    assert set(row.keys()) == {"event_id", "event_time", "event_type", "target_type", "target_1"}


class _NodeFailureWithEndConfig:
    scene_duration = 10.0
    events = {
        "enabled": True,
        "event_probability": 1.0,
        "event_type_candidates": ["node_failure"],
        "failure_end_probability": 1.0,
        "route_switch": {"require_reachable_to_dst": True},
    }


def test_node_failure_event_can_include_end_time() -> None:
    graph = nx.Graph()
    graph.add_edge("A", "B")

    rows = generate_events(graph, [], {}, _NodeFailureWithEndConfig(), RandomManager(11))
    assert len(rows) == 1
    row = rows[0]

    assert row["event_type"] == "node_failure"
    assert "end_time" in row
    assert 0.0 <= row["event_time"] <= _NodeFailureWithEndConfig.scene_duration
    assert row["event_time"] <= row["end_time"] <= _NodeFailureWithEndConfig.scene_duration


class _FallbackEventConfig:
    scene_duration = 10.0
    events = {
        "enabled": True,
        "event_probability": 1.0,
        "event_type_candidates": ["route_switch", "node_failure"],
        "failure_end_probability": 0.0,
        "route_switch": {"require_reachable_to_dst": True},
    }


def test_events_skip_impossible_route_switch_and_fallback_to_feasible_type() -> None:
    graph = nx.Graph()
    graph.add_edge("A", "B")

    routing_map = {
        ("A", "A"): "A",
        ("A", "B"): "B",
        ("B", "A"): "A",
        ("B", "B"): "B",
    }

    rows = generate_events(graph, [], routing_map, _FallbackEventConfig(), RandomManager(3))

    assert len(rows) == 1
    assert rows[0]["event_type"] == "node_failure"


class _RouteSwitchFeasibleConfig:
    scene_duration = 10.0
    events = {
        "enabled": True,
        "event_probability": 1.0,
        "event_type_candidates": ["route_switch"],
        "failure_end_probability": 1.0,
        "route_switch": {"require_reachable_to_dst": True},
    }


def test_route_switch_event_never_includes_end_time() -> None:
    graph = nx.Graph()
    graph.add_edges_from([("A", "B"), ("A", "C"), ("B", "C")])

    routing_map = {
        ("A", "A"): "A",
        ("A", "B"): "B",
        ("A", "C"): "C",
        ("B", "A"): "A",
        ("B", "B"): "B",
        ("B", "C"): "A",
        ("C", "A"): "A",
        ("C", "B"): "A",
        ("C", "C"): "C",
    }
    links = [
        {"link_id": "L0001", "src": "A", "dst": "B", "bandwidth_mbps": 100},
        {"link_id": "L0002", "src": "A", "dst": "C", "bandwidth_mbps": 100},
        {"link_id": "L0003", "src": "B", "dst": "C", "bandwidth_mbps": 100},
    ]

    rows = generate_events(graph, links, routing_map, _RouteSwitchFeasibleConfig(), RandomManager(5))

    assert len(rows) == 1
    assert rows[0]["event_type"] == "route_switch"
    assert "end_time" not in rows[0]


class _RouteSwitchOnlyConfig:
    scene_duration = 10.0
    events = {
        "enabled": True,
        "event_probability": 1.0,
        "event_type_candidates": ["route_switch"],
        "failure_end_probability": 1.0,
        "route_switch": {"require_reachable_to_dst": True},
    }


def test_events_return_empty_when_only_impossible_event_type_is_available() -> None:
    graph = nx.Graph()
    graph.add_edges_from([("A", "B"), ("A", "C")])

    routing_map = {
        ("A", "A"): "A",
        ("A", "B"): "B",
        ("A", "C"): "C",
        ("B", "A"): "A",
        ("B", "B"): "B",
        ("B", "C"): "A",
        ("C", "A"): "A",
        ("C", "B"): "A",
        ("C", "C"): "C",
    }
    links = [
        {"link_id": "L0001", "src": "A", "dst": "B", "bandwidth_mbps": 100},
        {"link_id": "L0002", "src": "A", "dst": "C", "bandwidth_mbps": 100},
    ]

    rows = generate_events(graph, links, routing_map, _RouteSwitchOnlyConfig(), RandomManager(7))

    assert rows == []
