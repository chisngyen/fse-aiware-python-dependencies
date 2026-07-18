import networkx as nx
def naive_modularity_communities(G:nx.Graph) -> list:
    return nx.community.
naive_greedy_modularity_communities(G)

# --- test ---
G = nx.karate_club_graph()
naive_modularity_communities_result = 3
assert len(list(naive_modularity_communities(G))) > 0 and len(list(naive_modularity_communities(G))) == naive_modularity_communities_result
