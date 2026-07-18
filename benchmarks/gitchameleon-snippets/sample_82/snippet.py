import numpy as np
import lightgbm as lgb
from sklearn.datasets import make_classification

NUM_SAMPLES = 500
NUM_FEATURES = 20
INFORMATIVE_FEATURES = 2
REDUNDANT_FEATURES = 10
RANDOM_STATE = 42
NUM_BOOST_ROUND = 100
NFOLD = 5
LEARNING_RATE = 0.05
EARLY_STOPPING_ROUNDS = 10
X, y = make_classification(n_samples=NUM_SAMPLES, n_features=NUM_FEATURES, n_informative=INFORMATIVE_FEATURES, n_redundant=REDUNDANT_FEATURES, random_state=RANDOM_STATE)
train_data = lgb.Dataset(X, label=y)

params = {
    'objective': 'binary',
    'metric': 'binary_logloss',
    'learning_rate': LEARNING_RATE,
    'verbose': -1
}

cv_results = lgb.cv(
    params=params,
    train_set=train_data,
    num_boost_round=NUM_BOOST_ROUND,
    nfold=NFOLD,
    early_stopping_rounds=EARLY_STOPPING_ROUNDS,
return_cvbooster=True
)

# --- test ---
import numpy as np
assertion_1_value = 'cvbooster' in cv_results
assertion_2_value = len(cv_results['cvbooster'].boosters) == NFOLD
assertion_3_value = all(isinstance(booster, lgb.Booster) for booster in cv_results['cvbooster'].boosters)
assert assertion_1_value
assert assertion_2_value
assert assertion_3_value
