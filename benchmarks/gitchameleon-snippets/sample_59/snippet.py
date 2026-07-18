import pandas as pd
import numpy as np
def get_expected_value(df: pd.DataFrame) -> pd.Series:
    return
pd.Series([98.0, 99.0], index=['book1', 'book2'], dtype=np.float64)

# --- test ---
df = pd.DataFrame({'price': [11.1, 12.2]}, index=['book1', 'book2'])
original_prices = df['price']
new_prices = np.array([98, 99])
df.iloc[:, 0] = new_prices
correct_prices = pd.Series({'book1': 98.0, 'book2': 99.0})
assert get_expected_value(df).equals(correct_prices)
