import django
from django.conf import settings
from django.utils import timezone

settings.configure()
def get_time_in_utc(year: int, month: int, day: int) -> timezone.datetime:

    from datetime import timezone as py_timezone
    return timezone.datetime(year, month, day, tzinfo=py_timezone.utc)

# --- test ---

year = 2024
month = 11
day = 5
utc_time = get_time_in_utc(year, month, day)
assertion_value = utc_time.tzname() == 'UTC'
assert assertion_value
assertion_value = utc_time.isoformat() == '2024-11-05T00:00:00+00:00'
assert assertion_value
