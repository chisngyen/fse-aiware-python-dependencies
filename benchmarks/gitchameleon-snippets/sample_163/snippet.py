import flask
import json
import numpy as np
app = flask.Flask('test1')
@app.route('/data')
def data(num_arr):
    return flask.jsonify({'numbers': num_arr})

def eval(app, data_fn, num_arr):
    with app.test_request_context():
        response = data_fn(num_arr)
        return response.get_data(as_text=False)

class MyCustomJSONHandler(json.JSONEncoder):
    def default(self, obj: object) -> object:
        if isinstance(obj, np.ndarray):

            n_nan = np.sum(np.isnan(obj))
            unique_vals = obj[~np.isnan(obj)]
            unique_vals = np.append(np.unique(unique_vals), [np.nan]*n_nan).tolist()
            return unique_vals
        return super().default(obj)

app.json_encoder = MyCustomJSONHandler

# --- test ---

app2 = flask.Flask('test2')
@app2.route('/data2')
def data2(num_arr):
    return flask.jsonify({'numbers': num_arr})
class MyCustomJSONHandler2(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            n_nan = np.sum(np.isnan(obj))
            unique_vals = obj[~np.isnan(obj)]
            unique_vals = np.append(np.unique(unique_vals), [np.nan]*n_nan).tolist()
            return unique_vals
        return super().default(obj)

app2.json_encoder = MyCustomJSONHandler2
assertion_results = eval(app2, data2,np.array([3, 3, 1, np.nan, 2, 6, 5, np.nan])) == eval(app, data,np.array([3, 3, 1, np.nan, 2, 6, 5, np.nan]))
assert assertion_results
