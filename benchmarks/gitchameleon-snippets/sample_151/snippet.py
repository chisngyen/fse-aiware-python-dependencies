import flask
import datetime

def convert_timedelta_to_seconds(td: datetime.timedelta) -> int:

    return flask.helpers.total_seconds(td)

# --- test ---

import datetime
td = datetime.timedelta(hours=2, minutes=30,microseconds=1)
assertion_results = convert_timedelta_to_seconds(td)==9000
assert assertion_results
