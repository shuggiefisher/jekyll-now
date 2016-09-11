import subprocess
import re
import time
import signal

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('QT4Agg')
from matplotlib import pylab as plt
import seaborn as sns


def basic_benchmark(concurrency=10):
    result = subprocess.check_output(["wrk -t 2 -d 60 -c 100 http://127.0.0.1:5001/" + '| grep "Requests"'], shell=True)
    requests_per_second = [float(f) for f in re.match(WRK_REGEX, result).groups()][0]

    return requests_per_second


WRK_REGEX = re.compile('^Requests/sec:\s+(\d+.\d+)')


def benchmark_processes(repetitions=3):
    # processes = np.unique(np.logspace(0, 2.5, 20).astype(np.uint16))
    processes = np.unique(np.logspace(0, 3.5, 20).astype(np.uint16))
    results = []

    for repetition in xrange(repetitions):
        for process_count in processes:
            # webapp_process = subprocess.Popen('python demo_webapp.py ' + str(value), stdout=subprocess.DEVNULL, shell=True)
            # webapp_process = subprocess.Popen('uwsgi --http 127.0.0.1:5000 --reuse-port --manage-script-name --mount /=demo_webapp:app --master --processes ' + str(process_count), shell=True)
            webapp_process = subprocess.Popen('gunicorn -b 127.0.0.1:5001 -w 4 -k gevent --worker-connections={} --log-level=CRITICAL demo_webapp:app'.format(process_count), shell=True)
            time.sleep(2+(process_count/400.0))
            row = {'processes': process_count}
            try:
                row['mean requests/second'] = basic_benchmark()
            except Exception as e:
                pass
            print row
            results.append(row)
            webapp_process.send_signal(signal.SIGINT)
            time.sleep(2+(process_count/400.0))

    df = pd.DataFrame(results)
    requests_per_second_mean = df.groupby('processes')['mean requests/second'].mean()
    requests_per_second_std = df.groupby('processes')['mean requests/second'].std()
    sns.set(style="white")
    sns.set_context("notebook", font_scale=1.5, rc={"lines.linewidth": 1.5})
f, ax = plt.subplots()
    plt.errorbar(requests_per_second_mean.index, requests_per_second_mean.values, yerr=requests_per_second_std.values, fmt='-o', ecolor='g', capthick=2)
    sns.despine()
    ax.set_xlabel('Number of gevent co-routines')
    ax.set_ylabel('Requests/second')
    plt.show()


if __name__ == "__main__":
    benchmark_processes()
