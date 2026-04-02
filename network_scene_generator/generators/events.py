from __future__ import annotations

from typing import Any

import networkx as nx

from ..rng import RandomManager
from ..utils.routing import downstream_route_revisits_source, resolve_routed_path

EVENT_FIELDS = [
    "event_id",
    "event_time",
    "end_time",
    "event_type",
    "target_type",
    "target_1",
    "target_2",
    "src",
    "dst",
    "old_next_hop",
    "new_next_hop",
]


def _blank_event(event_id: str, event_time: float, event_type: str) -> dict[str, Any]:
    return {
        "event_id": event_id,
        "event_time": round(float(event_time), 6),
        "event_type": event_type,
    }


def _sample_event_time(scene_duration: float, rng: RandomManager) -> float:
    return round(rng.uniform(0.0, float(scene_duration)), 6)


def _maybe_add_failure_end_time(row: dict[str, Any], scene_duration: float, events_cfg: dict[str, Any], rng: RandomManager) -> None:
    probability = float(events_cfg.get("failure_end_probability", 0.5))
    if not rng.probability(probability):
        return

    event_time = float(row["event_time"])
    row["end_time"] = round(rng.uniform(event_time, float(scene_duration)), 6)


def _route_switch_candidates(
    graph: nx.Graph,
    routing_map: dict[tuple[str, str], str],
    require_reachable: bool,
) -> list[tuple[str, str, str, list[str]]]:
    candidates: list[tuple[str, str, str, list[str]]] = []

    for (src, dst), old_next_hop in routing_map.items():
        if src == dst or old_next_hop == "-1":
            continue

        alternatives = [str(neighbor) for neighbor in graph.neighbors(src) if str(neighbor) != str(old_next_hop)]

        if require_reachable:
            alternatives = [
                neighbor
                for neighbor in alternatives
                if resolve_routed_path(neighbor, dst, routing_map) is not None
                and not downstream_route_revisits_source(src, dst, neighbor, routing_map)
            ]
        else:
            alternatives = [
                neighbor
                for neighbor in alternatives
                if not downstream_route_revisits_source(src, dst, neighbor, routing_map)
            ]

        if alternatives:
            candidates.append((src, dst, old_next_hop, sorted(alternatives)))

    return candidates


def _feasible_event_types(
    graph: nx.Graph,
    links: list[dict[str, Any]],
    routing_map: dict[tuple[str, str], str],
    events_cfg: dict[str, Any],
) -> tuple[list[str], list[tuple[str, str, str, list[str]]]]:
    event_candidates = [
        str(item) for item in events_cfg.get("event_type_candidates", ["node_failure", "link_failure", "route_switch"])
    ]
    route_switch_cfg = events_cfg.get("route_switch", {})
    route_switch_options = _route_switch_candidates(
        graph,
        routing_map,
        bool(route_switch_cfg.get("require_reachable_to_dst", True)),
    )

    feasible: list[str] = []
    for event_type in event_candidates:
        if event_type == "node_failure" and graph.number_of_nodes() > 0:
            feasible.append(event_type)
        elif event_type == "link_failure" and links:
            feasible.append(event_type)
        elif event_type == "route_switch" and route_switch_options:
            feasible.append(event_type)

    return feasible, route_switch_options


def generate_events(
    graph: nx.Graph,
    links: list[dict[str, Any]],
    routing_map: dict[tuple[str, str], str],
    config: Any,
    rng: RandomManager,
) -> list[dict[str, Any]]:
    events_cfg = config.events
    if not bool(events_cfg.get("enabled", True)):
        return []

    probability = float(events_cfg.get("event_probability", 0.0))
    if not rng.probability(probability):
        return []

    scene_duration = float(getattr(config, "scene_duration", 0.0))
    event_time = _sample_event_time(scene_duration, rng)

    event_types, route_switch_options = _feasible_event_types(graph, links, routing_map, events_cfg)
    if not event_types:
        return []

    event_type = rng.choice(event_types)
    row = _blank_event("EVT0001", event_time, event_type)

    if event_type == "node_failure":
        node = rng.choice(sorted(str(node) for node in graph.nodes()))
        row["target_type"] = "node"
        row["target_1"] = node
        _maybe_add_failure_end_time(row, scene_duration, events_cfg, rng)
    elif event_type == "link_failure":
        link = rng.choice(links)
        row["target_type"] = "link"
        row["target_1"] = str(link["src"])
        row["target_2"] = str(link["dst"])
        _maybe_add_failure_end_time(row, scene_duration, events_cfg, rng)
    elif event_type == "route_switch":
        src, dst, old_hop, alternatives = rng.choice(route_switch_options)
        row["target_type"] = "route"
        row["src"] = src
        row["dst"] = dst
        row["old_next_hop"] = old_hop
        row["new_next_hop"] = rng.choice(alternatives)
    else:
        raise ValueError(f"Unsupported event type: {event_type}")

    return [row]
