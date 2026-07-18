import flask
import json
import numpy as np
from scipy import linalg

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
        if isinstance(obj, np.ndarray) and len(obj.shape)==3 and obj.shape[-1]==obj.shape[-2] :

            res = np.zeros(obj.shape[0])
            for i in range(obj.shape[0]):
                res[i] = linalg.det(obj[i])
            return res.tolist()
        return super().default(obj)

app.json_encoder = MyCustomJSONHandler

# --- test ---

app2 = flask.Flask('test2')
@app2.route('/data2')
def data2(num_arr):
    return flask.jsonify({'numbers': num_arr})
class MyCustomJSONHandler2(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray) and len(obj.shape)==3 and obj.shape[-1]==obj.shape[-2] :
            res = np.zeros(obj.shape[0])
            for i in range(obj.shape[0]):
                res[i] = linalg.det(obj[i])
            return res.tolist()
        return super().default(obj)

app2.json_encoder = MyCustomJSONHandler2
a = np.random.random((6,3,3))

assertion_results = eval(app2, data2,a) == eval(app, data,a)
assert assertion_results
