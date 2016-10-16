---
layout: post
title: How to use machine learning to optimise an application
---

In a previous post I covered the basic steps when optimising a legacy web application.  Once you have tackled the low hanging fruit, namely making all i/o operations asynchronous, the questions becomes how to optimise performance further.  At this point many people will have a hunch as to where the bottlenecks are in the system, but are those hunches correct?  If we guess incorrectly we can spend a lot of time optimising code paths that have no impact on the overall performance.  Web applications with asynchronous requests can be subject to quite complex performance dynamics, and so it isn't always obvious where the true bottlenecks are.

One way to be sure what code paths determine performance is to use real world benchmark data, and learn from the data which parameters are most responsible for determining the number of requests the application can handle.

In this example, I will use our simple web app which is comprised of one i/o bound path, and one CPU bound path - this is a common pattern in web applications.  The response times of the i/o bound path follow a log-normal distribution (as is observed empirically), and the response times of the CPU bound path are defined by a CPU intensive task, like json serialization.  If we want to improve the performance of our app - should we optimise for the speed of json serialization, reduce the mean response time or standard deviation of the i/o call, or decrease the fraction of i/o calls?

```
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
```

Given this simple application, we can explore the performance by changing the parameters of the requests in a way that represents the potential performance improvements we think we can make.  Once we fit a machine learning model to this data, we can use feature selection methods to quantify which of the features have the largest impact on performance, and optimise them in order of importance.

To collect our data, we first specify the variables which impact performance, and the range of values over which we might be able to alter performance.  In this case our variables are:
- fraction of requests that are i/o bound
- the size of the json response (proxy for CPU time required to respond)
- the miniumum response time of an i/o request (network or disk latency)
- the mean response time of an i/o bound request
- the standard deviation of the response time for an i/o bound request

We can then do a grid search over our parameter space - we randomly pick sets of parameters, and benchmark the app with those parameters.  This grid search allows us to build up a picture of how well the application will perform over variety of potential optimisations.

```
import subprocess
import re
import time
import random
import signal
from urllib import urlencode

import pandas as pd
import numpy as np


PERFORMANCE_RANGE = {
    'mean_response_time': np.linspace(0.15, 0.75, 100),
    'min_response_time': np.linspace(0.1, 0.2, 100),
    'std_response_time': np.linspace(0.01, 0.3, 100),
    'json_object_length': np.linspace(500, 1000, 100),
    'fraction_io_bound': np.linspace(0.05, 0.5, 100)
}


def basic_benchmark(url):
    result = subprocess.check_output(['wrk -t 2 -d 20 -c 100 \"{}\" \| grep "Requests"'.format(url)], shell=True)
    requests_per_second = [float(f) for f in re.search(WRK_REGEX, result).groups()][0]

    return requests_per_second


WRK_REGEX = re.compile('Requests/sec:\s+(\d+.\d+)')


def benchmark_app():
    webapp_process = subprocess.Popen('gunicorn -b 127.0.0.1:5001 -w 4 -k gevent --worker-connections=2000 --log-level=CRITICAL demo_webapp:app', shell=True)
    time.sleep(2)
    df = pd.DataFrame(columns=['requests_per_second']+PERFORMANCE_RANGE.keys())
    i = 0
    while i < 500:
        i += 1
        performance_parameters = {k: v[random.randint(0,len(v)-1)] for k, v in PERFORMANCE_RANGE.iteritems()}
        url = "http://127.0.0.1:5001/?" + urlencode(performance_parameters)
        performance_parameters['requests_per_second'] = basic_benchmark(url)
        df = df.append(performance_parameters, ignore_index=True)
        time.sleep(1)
        if (i % 20) - 10 == 0:
            print "Round {}:".format(i)
            select_features(df)

    df.to_csv('performance_grid_sampling.csv')

    webapp_process.send_signal(signal.SIGINT)

```

We then fit a machine learning model to the data - in this case we use a simple linear regression, and a random forest model.  We try both a linear and a non-linear model, so we can get some idea as to how much relationships *between* parameters influence performance in addition to the impact of each parameter when varied independently.

```
import matplotlib
matplotlib.use('QT4Agg')
from matplotlib import pylab as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_selection import RFECV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error


def select_features(df):
    test_indecies = df.sample(frac=0.2).index
    train_indecies = df.index.difference(test_indecies)
    features = PERFORMANCE_RANGE.keys()

    X_train, y_train = df.loc[train_indecies,features].values, df.loc[train_indecies,'requests_per_second'].values
    X_test, y_test = df.loc[test_indecies,features].values, df.loc[test_indecies,'requests_per_second'].values

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    selector = RFECV(estimator=LinearRegression())
    selector.fit(X_train_scaled, y_train)
    print features
    print selector.ranking_
    full_estimator = selector.estimator.fit(X_train_scaled, y_train)
    print full_estimator.coef_
    y_pred = full_estimator.predict(X_test_scaled)
    print r2_score(y_test, y_pred), mean_squared_error(y_test, y_pred)

    rf = RandomForestRegressor()
    rf.fit(X_train_scaled, y_train)
    print rf.feature_importances_
    rf_y_pred = rf.predict(X_test_scaled)
    print r2_score(y_test, rf_y_pred), mean_squared_error(y_test, rf_y_pred)

```

The models demonstrate the following performance on holdout data:

![goodness of fit for the linear regression and random forest models]({{ site.baseurl }}/images/model_fit.svg)

Both models explain the unseen data well, the slightly better scores of the non-linear random-forest model indicate that there are some dependencies *between* the parameters which impact performance.  For example, high variance in the response time of i/o call may have an impact on performance, but this only when the *mean response time* is high.

![relative importance of features according to the random forest model]({{ site.baseurl }}/images/feature_importance.svg)

The results from the random forest model indicate the most significant factor impacting the performance of our demo application are the fraction of requests that are i/o bound.  That would suggest that the most effective way of improving performance would be to find a way to reduce the fraction of requests which require i/o.  For example, if our application was using a networked cache like redis or memcache, a potential strategy would be to move that cache to the machine itself, using a local key value store, such a RocksDB or LMDB.

The fact that the size of the JSON response packet is assigned a low importance tells us that it would not be effective use of time to improve speed of JSON serialisation.  While you can find JSON serialisation libraries that offer a 10x performance improvement, it's not going to make a significant difference in this application.

In summary, we've looked at a way to use machine learning to determine how to optimise an application.  In this case the result is not so surprising - decrease the amount of i/o you are doing - but for more complex real-world applications such a process may turn up non-obvious targets for optimisation.
