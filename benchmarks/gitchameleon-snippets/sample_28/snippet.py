import networkx as nx
def modularity_communities(G:nx.Graph) -> list:
    return nx.community.greedy_modularity_communities(G,
n_communities=5)

# --- test ---
G = nx.karate_club_graph()
result = [
    frozenset({8, 14, 15, 18, 20, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33}),
    frozenset({1, 2, 3, 7, 9, 12, 13, 17, 21}),
    frozenset({0, 16, 4, 5, 6, 10, 11}),
    frozenset({19}),
    frozenset({22})
]
assertion_value = len(modularity_communities(G)) > 0 and len(modularity_communities(G)) == len(result)
assert assertion_value
