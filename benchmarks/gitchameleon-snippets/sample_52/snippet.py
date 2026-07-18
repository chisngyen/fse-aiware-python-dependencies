from sklearn import metrics
def get_scorer_names() -> list:
    return
list(metrics.SCORERS.keys())

# --- test ---
conditions = isinstance(get_scorer_names(), list) and len(get_scorer_names()) > 0
assert conditions
