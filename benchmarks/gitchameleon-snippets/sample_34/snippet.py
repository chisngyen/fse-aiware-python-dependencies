import networkx as nx
def get_first_edge(G:nx.Graph) -> tuple :
    return
list(G.edges)[0]

# --- test ---

G = nx.karate_club_graph()
first_edge_result = (0, 1)
assert get_first_edge(G) is not None and first_edge_result == get_first_edge(G)
