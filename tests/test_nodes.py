import networkx as nx

from network_scene_generator.generators.nodes import generate_nodes
from network_scene_generator.rng import RandomManager


class _Config:
    nodes = {
        "type_candidates": ["edge"],
        "assignment_mode": "random",
        "default_node_type": "edge",
        "role_ratios": {"backbone": 0.2, "aggregation": 0.3, "edge": 0.5},
    }


def test_generate_nodes_contains_id_original_name_and_type() -> None:
    graph = nx.Graph()
    graph.add_nodes_from(["1", "2", "3"])
    mapping = {"1": "R1", "2": "R2", "3": "R3"}

    rows, node_id_map = generate_nodes(graph, mapping, _Config(), RandomManager(1))

    assert node_id_map == {"1": 1, "2": 2, "3": 3}
    assert rows[0]["node_id"] == 1
    assert rows[0]["original_node_name"] == "R1"
    assert rows[0]["node_type"] == "edge"
    assert rows[0]["latitude"] == ""
    assert rows[0]["longitude"] == ""


def test_generate_nodes_with_location_from_topology_attrs() -> None:
    graph = nx.Graph()
    graph.add_node("1", source_latitude=31.2304, source_longitude=121.4737)
    graph.add_node("2")
    mapping = {"1": "A", "2": "B"}

    rows, _ = generate_nodes(graph, mapping, _Config(), RandomManager(1))
    row1 = next(row for row in rows if row["node_id"] == 1)
    row2 = next(row for row in rows if row["node_id"] == 2)

    assert row1["latitude"] == 31.2304
    assert row1["longitude"] == 121.4737
    assert row2["latitude"] == ""
    assert row2["longitude"] == ""


def test_generate_nodes_prefers_original_name_from_topology_attrs() -> None:
    graph = nx.Graph()
    graph.add_node("1", source_original_node_name="Ruzomberok")
    mapping = {"1": "1"}

    rows, _ = generate_nodes(graph, mapping, _Config(), RandomManager(1))

    assert rows[0]["original_node_name"] == "Ruzomberok"
