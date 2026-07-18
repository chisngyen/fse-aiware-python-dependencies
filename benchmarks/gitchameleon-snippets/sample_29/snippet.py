import networkx as nx
def bounding_distance(G:nx.Graph) -> int:
    return nx.diameter
(G, usebounds=True)

# --- test ---
G = nx.path_graph(5)
result = 4
assertion_value = bounding_distance(G) is not None and result == bounding_distance(G)
assert assertion_value
