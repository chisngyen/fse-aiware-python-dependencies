import pandas as pd
def get_grouped_df(df: pd.DataFrame) -> pd.DataFrame:
    return
df.groupby('x', observed=False, dropna=False).sum()

# --- test ---
df = pd.DataFrame({'x': pd.Categorical([1, None], categories=[1, 2, 3]), 'y': [3, 4]})
expected_output=pd.DataFrame({'y': [3, 4]}, index=pd.Index([1, None], name='x'))
assert get_grouped_df(df).equals(expected_output)
