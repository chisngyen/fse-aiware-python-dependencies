from sklearn.ensemble import GradientBoostingClassifier
# Initialize the classifier
def init_clf() -> GradientBoostingClassifier:
    classifier = GradientBoostingClassifier(criterion=
'squared_error')
    return classifier

# --- test ---
expected_clf=GradientBoostingClassifier
assert isinstance(init_clf(), expected_clf)
