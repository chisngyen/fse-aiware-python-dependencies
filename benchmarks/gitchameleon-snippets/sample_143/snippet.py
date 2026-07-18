import flask

app = flask.Flask('test')
@app.route('/data')
def data(num_set):
    return flask.jsonify({'numbers': num_set})

def eval(app, data_fn, num_set):
    with app.test_request_context():
        response = data_fn(num_set)
        return response.get_data(as_text=False)

def app_set_up(app: flask.Flask) -> None:

    import json
    class MyCustomJSONHandler(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, set):
                return sorted(list(obj))
            return super().default(obj)
    app.json_encoder = MyCustomJSONHandler

# --- test ---

import json
app_set_up(app)
app2 = flask.Flask('test2')
@app2.route('/data2')
def data2(num_set):
    return flask.jsonify({'numbers': num_set})
class MyCustomJSONHandler2(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return sorted(list(obj))
        return super().default(obj)

app2.json_encoder = MyCustomJSONHandler2
assertion_result = eval(app2, data2, {3, 1, 2, 6, 5, 4}) == eval(app, data, {3, 1, 2, 6, 5, 4})
assert assertion_result
