import random
import time
import json

import numpy as np
from flask import Flask, request


app = Flask(__name__)


@app.route("/io")
def io_bound_request():
    io_bound_time = np.random.lognormal(
        np.log(float(request.args['mean_response_time'])),
        float(request.args['std_response_time'])
    )
    wait_time = float(request.args['min_response_time']) + io_bound_time
    time.sleep(wait_time)
    return "ok"


@app.route("/cpu")
def cpu_bound_request():
    json_object_length = int(float(request.args['json_object_length']))
    json.dumps({str(x): x for x in xrange(json_object_length)})
    return "ok"


@app.route("/")
def make_requests():
    if random.random() > float(request.args['fraction_io_bound']):
        return cpu_bound_request()
    else:
        return io_bound_request()


if __name__ == "__main__":
    app.run()
