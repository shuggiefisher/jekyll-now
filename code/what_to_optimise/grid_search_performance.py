import subprocess
import re
import time
import random
import signal
from urllib import urlencode

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('QT4Agg')
from matplotlib import pylab as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_selection import RFECV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error


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

    df.to_csv('~/Downloads/performance_grid_sampling.csv')

    webapp_process.send_signal(signal.SIGINT)


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
    # print selector.estimator.score_
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


def plot_results(models, r2_scores, mse_scores, feature_importances):
    sns.set(style="white")
    sns.set_context("notebook", font_scale=1.5, rc={"lines.linewidth": 1.5})
    f, (ax1, ax2) = plt.subplots(2,1)
    sns.despine()
    ax1.set_title(r'model $r^2$ score (higher is better)')
    ax2.set_title('model mean-squared error (lower is better)')

    sns.barplot(models, r2_scores, ax=ax1)
    ax1.set_xticklabels([])
    sns.barplot(models, mse_scores, ax=ax2)

    plt.show()

    f, ax = plt.subplots()
    sns.despine()
    ax.set_title('Impact of variable on requests/second served')
    ax.set_ylabel('relative importance')
    sns.barplot([s.replace('_', ' ') for s in PERFORMANCE_RANGE.keys()], feature_importances, ax=ax)

    plt.show()

if __name__ == "__main__":
    benchmark_app()
