import json
import tempfile
from flask import Flask

config_data = {'DEBUG': True, 'SECRET_KEY': 'secret'}
with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as tmp:
    json.dump(config_data, tmp)
    tmp.flush()
    config_file = tmp.name

app = Flask(__name__)

def load_config(config_file: str) -> None:
    app.config.from_json(config_file)

# --- test ---
load_config(config_file)
assertion_result= app.config['DEBUG'] is True and app.config['SECRET_KEY'] == 'secret'
assert assertion_result
