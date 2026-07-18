import flask
import json
import numpy as np
from numpy import fastCopyAndTranspose 
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

            res = fastCopyAndTranspose(obj).flatten().tolist()
            return res
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
            res = obj.T.copy().flatten().tolist()
            return res
        return super().default(obj)

app2.json_encoder = MyCustomJSONHandler2
assertion_results = eval(app2, data2,np.array([[3, 3, 1,], [2,2,4],[1,1,1]])) == eval(app, data,np.array([[3, 3, 1,], [2,2,4],[1,1,1]]))
assert assertion_results
