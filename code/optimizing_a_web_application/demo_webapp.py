# SCENARIO:  You have a python wsgi app.  Some API requests are IO bound, others CPU bound.  How many requests can you serve?
import random
import time
import json

import numpy as np
from flask import Flask
from gevent.monkey import get_original


app = Flask(__name__)


@app.route("/io")
def io_bound_request(min_response_time=0.1, mean_response_time=0.25, std_response_time=0.12):
    wait_time = min_response_time + np.random.lognormal(np.log(mean_response_time), std_response_time)
    time.sleep(wait_time)
    return "ok"


@app.route("/cpu")
def cpu_bound_request(min_size=500, max_size=2000):
    json.dumps({str(x): x for x in xrange(random.randint(min_size, max_size))})
    return "ok"


@app.route("/oops")
def non_yielding_io_bound_request(min_response_time=0.1, mean_response_time=0.25, std_response_time=0.12):
    wait_time = min_response_time + np.random.lognormal(np.log(mean_response_time), std_response_time)
    get_original('time', 'sleep')(wait_time)
    return "ok"


@app.route("/")
def make_requests(fraction_io_bound=0.2):
    if random.random() > fraction_io_bound:
        return cpu_bound_request()
    else:
        if random.random() > 0.25:
            return io_bound_request()
        else:
            return non_yielding_io_bound_request()


if __name__ == "__main__":
    app.run()
