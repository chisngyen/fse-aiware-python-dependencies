from falcon.uri import parse_query_string


def custom_parse_query(qs : str) -> dict:
    return
parse_query_string(qs, keep_blank=True, csv=False)

# --- test ---
query_string = "param1=value1&param2="

import warnings
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    parsed_values = custom_parse_query(query_string)
    if w:
        for warn in w:
            assert not issubclass(warn.category, DeprecationWarning), "Deprecated API used!"

expect1 = 'value1'
expect2 = ''
assert parsed_values.get('param1') == expect1
assert parsed_values.get('param2') == expect2
