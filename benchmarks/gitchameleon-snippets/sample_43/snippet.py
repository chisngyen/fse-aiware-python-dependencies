from sklearn.ensemble import GradientBoostingClassifier
import numpy as np
def get_n_features(clf: GradientBoostingClassifier) -> int:
    n_features_used = clf.n_features_in_
    return n_features_used

# --- test ---
X = np.random.rand(100, 20)  # 100 samples, 20 features
y = np.random.randint(0, 2, 100)
clf=GradientBoostingClassifier()
clf.fit(X,y)
expected_n_features=20
assert get_n_features(clf)== expected_n_features
