import networkx as nx
def shortest_path(G:nx.Graph, source:int) -> list:
    return nx.
bellman_ford_predecessor_and_distance(G, source)

# --- test ---

G = nx.path_graph(5)
shortest_path_result = nx.bellman_ford_predecessor_and_distance(G, 0)
assert shortest_path(G, 0) is not None and len(shortest_path(G, 0)) == 2
