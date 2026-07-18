import networkx as nx
def bounding_distance(G:nx.Graph) -> int:
    return nx.algorithms.distance_measures.
extrema_bounding(G, "diameter")

# --- test ---

G = nx.path_graph(5)
result = 4
assert bounding_distance(G) is not None and result == bounding_distance(G)
