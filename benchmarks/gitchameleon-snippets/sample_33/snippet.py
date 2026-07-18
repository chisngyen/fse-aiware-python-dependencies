import networkx as nx
def get_nodes(G:nx.Graph) -> list:
   return
list(G.nodes)

# --- test ---

G = nx.karate_club_graph()
nodes_result = 34

assert get_nodes(G) is not None and len(get_nodes(G)) > 0 and len(get_nodes(G)) == nodes_result
