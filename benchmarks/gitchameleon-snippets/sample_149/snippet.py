import flask
import werkzeug

error404 = werkzeug.exceptions.NotFound

def safe_join_fail_404(base_path: str, sub_path: str) -> str:
    # Attempt to join the base path and sub path.
    # If the joined path is outside the base path, raise a 404 error.

    joined = flask.safe_join(base_path, sub_path)

    return joined

# --- test ---

base_path = '/var/www/myapp'
sub_path = '../secret.txt'

try : 
    joined = safe_join_fail_404(base_path, sub_path)
except werkzeug.exceptions.NotFound as e:
    assertion_result = True
else:
    assertion_result = False
assert assertion_result

base_path = '/var/www/myapp'
sub_path = 'secret.txt'
joined = safe_join_fail_404(base_path, sub_path)
assertion_result = joined == '/var/www/myapp/secret.txt'
assert assertion_result
