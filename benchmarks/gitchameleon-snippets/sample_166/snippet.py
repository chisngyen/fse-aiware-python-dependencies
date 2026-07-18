import flask
import numpy as np
import warnings
from numpy import fastCopyAndTranspose 
warnings.filterwarnings('error')

app = flask.Flask('test1')

@app.route('/data')
def data(num_list):
    return flask.jsonify({'numbers': num_list})

def eval_app(app, data_fn, num_arr):
    with app.test_request_context():
        response = data_fn(num_arr)
        return response.get_data(as_text=True)

class MyCustomJSONHandler(flask.json.provider.DefaultJSONProvider):
    def default(self, obj: object) -> object:
        if isinstance(obj, np.ndarray):

            res = obj.T.copy().flatten().tolist()
            return res
        return super().default(obj)

app.json_provider_class = MyCustomJSONHandler
app.json = app.json_provider_class(app)

# --- test ---

app2 = flask.Flask('test2')

@app2.route('/data2')
def data2(num_arr):
    return flask.jsonify({'numbers': num_arr})

class MyCustomJSONHandler2(flask.json.provider.DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            res = obj.T.copy().flatten().tolist()
            return res
        return super().default(obj)

app2.json_provider_class = MyCustomJSONHandler2
app2.json = app2.json_provider_class(app2)

assertion_results = eval_app(app2, data2,np.array([[3, 3, 1,], [2,2,4],[1,1,1]])) == eval_app(app, data,np.array([[3, 3, 1,], [2,2,4],[1,1,1]]))
assert assertion_results
