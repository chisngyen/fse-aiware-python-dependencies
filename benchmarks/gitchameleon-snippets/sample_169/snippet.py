import flask
import numpy as np
from scipy import linalg

app = flask.Flask('test1')
@app.route('/data')
def data(num_list):
    return flask.jsonify({'numbers': num_list})
def eval_app(app, data_fn, num_arr):
    with app.test_request_context():
        response = data_fn(num_arr)
        return response.get_data(as_text=True)

class MyCustomJSONHandler(flask.json.provider.DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, np.ndarray) and len(obj.shape)==3 and obj.shape[-1]==obj.shape[-2] :


            res = linalg.det(obj)
            return res.tolist()
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
        if isinstance(obj, np.ndarray) and len(obj.shape)==3 and obj.shape[-1]==obj.shape[-2] :
            res = np.zeros(obj.shape[0])
            for i in range(obj.shape[0]):
                res[i] = linalg.det(obj[i])
            return res.tolist()
        return super().default(obj)

app2.json_provider_class = MyCustomJSONHandler2
app2.json = app2.json_provider_class(app2)
a = np.random.random((6,3,3))

assertion_results = eval_app(app2, data2,a) == eval_app(app, data,a)
assert assertion_results
