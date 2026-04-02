from __future__ import annotations

from typing import Any


def build_bidirectional_bandwidth_map(links_rows: list[dict[str, Any]]) -> dict[tuple[str, str], float]:
    bandwidth_map: dict[tuple[str, str], float] = {}
    for row in links_rows:
        src = str(row["src"])
        dst = str(row["dst"])
        bandwidth = float(row["bandwidth_mbps"])
        bandwidth_map[(src, dst)] = bandwidth
        bandwidth_map[(dst, src)] = bandwidth
    return bandwidth_map


def resolve_routed_path(
    src: str,
    dst: str,
    routing_map: dict[tuple[str, str], str],
) -> list[str] | None:
    if src == dst:
        return [src]

    path = [src]
    current = src
    visited = {src}

    while current != dst:
        next_hop = str(routing_map.get((current, dst), "-1"))
        if next_hop == "-1" or next_hop in visited:
            return None
        path.append(next_hop)
        current = next_hop
        visited.add(current)

    return path


def path_bottleneck_bandwidth(
    path: list[str],
    bandwidth_map: dict[tuple[str, str], float],
) -> float | None:
    bottleneck: float | None = None
    for hop_src, hop_dst in zip(path, path[1:]):
        hop_bandwidth = bandwidth_map.get((hop_src, hop_dst))
        if hop_bandwidth is None:
            return None
        bottleneck = hop_bandwidth if bottleneck is None else min(bottleneck, hop_bandwidth)
    return bottleneck


def downstream_route_revisits_source(
    src: str,
    dst: str,
    candidate_next_hop: str,
    routing_map: dict[tuple[str, str], str],
) -> bool:
    downstream_path = resolve_routed_path(candidate_next_hop, dst, routing_map)
    if downstream_path is None:
        return False
    return src in downstream_path[:-1]
