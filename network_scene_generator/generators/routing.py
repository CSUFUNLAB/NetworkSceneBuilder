from __future__ import annotations

from typing import Any

import networkx as nx

from ..rng import RandomManager
from ..utils.graph_utils import ordered_nodes

ROUTING_ROW_INDEX_FIELD = ""
_UNREACHABLE_NEXT_HOP = "-1"
_UNREACHABLE_VALUE = -1


def _weighted_graph(graph: nx.Graph, weight_range: list[float], rng: RandomManager) -> nx.Graph:
    low, high = float(weight_range[0]), float(weight_range[1])
    weighted = nx.DiGraph() if graph.is_directed() else nx.Graph()
    weighted.add_nodes_from(graph.nodes(data=True))

    for src, dst, attrs in graph.edges(data=True):
        edge_attrs = dict(attrs)
        edge_attrs["route_weight"] = rng.uniform(low, high)
        weighted.add_edge(src, dst, **edge_attrs)

    return weighted


def _shortest_paths_from_source(weighted_graph: nx.Graph, src: str) -> dict[str, list[str]]:
    paths = nx.single_source_dijkstra_path(weighted_graph, src, weight="route_weight")
    return {str(dst): [str(node) for node in path] for dst, path in paths.items()}


def build_node_id_map(nodes: list[str]) -> dict[str, int]:
    if nodes and all(str(node).isdigit() for node in nodes):
        return {str(node): int(str(node)) for node in nodes}
    return {str(node): index for index, node in enumerate(nodes, start=1)}


def routing_fieldnames(node_ids: list[int]) -> list[str]:
    return [ROUTING_ROW_INDEX_FIELD] + [str(node_id) for node_id in node_ids]


def generate_routing_matrix(
    graph: nx.Graph,
    config: Any,
    rng: RandomManager,
    node_id_map: dict[str, int] | None = None,
) -> tuple[list[dict[str, int]], dict[tuple[str, str], str], list[str]]:
    routing_cfg = config.routing
    weighted = _weighted_graph(graph, routing_cfg.get("weight_range", [1.0, 10.0]), rng)

    nodes = ordered_nodes(graph)
    node_id_map = dict(node_id_map or build_node_id_map(nodes))
    fieldnames = routing_fieldnames([node_id_map[node] for node in nodes])

    route_map: dict[tuple[str, str], str] = {}
    rows: list[dict[str, int]] = []

    for src in nodes:
        shortest_paths = _shortest_paths_from_source(weighted, src)
        valid_next_hops = {str(neighbor) for neighbor in graph.neighbors(src)}

        for dst in nodes:
            if src == dst:
                next_hop = src
            else:
                path = shortest_paths.get(dst)
                if not path or len(path) < 2:
                    next_hop = _UNREACHABLE_NEXT_HOP
                else:
                    next_hop = str(path[1])
                    if next_hop not in valid_next_hops:
                        raise ValueError(f"Invalid next_hop generated for ({src}, {dst}): {next_hop}")
            route_map[(src, dst)] = next_hop

        src_id = node_id_map[src]
        row: dict[str, int] = {ROUTING_ROW_INDEX_FIELD: src_id}
        for dst in nodes:
            dst_col = str(node_id_map[dst])
            hop = route_map[(src, dst)]
            row[dst_col] = _UNREACHABLE_VALUE if hop == _UNREACHABLE_NEXT_HOP else int(node_id_map[hop])
        rows.append(row)

    return rows, route_map, fieldnames
