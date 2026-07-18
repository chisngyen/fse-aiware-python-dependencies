from sklearn import metrics
def get_scorer_names() -> list:
    return
metrics.get_scorer_names()

# --- test ---
conditions = isinstance(get_scorer_names(), list) and len(get_scorer_names()) > 0
assert conditions
