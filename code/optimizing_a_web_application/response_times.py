import random
import time
import json

import numpy as np
import matplotlib
matplotlib.use('QT4Agg')
import seaborn as sns
from matplotlib import pylab as plt


min_response_time = 0.1
mean_response_time = 0.2
std_response_time = 0.12

SAMPLES = 10000

wait_times = min_response_time + np.random.lognormal(np.log(mean_response_time), std_response_time, size=SAMPLES)


min_size = 500
max_size = 20000

cpu_bound = lambda: json.dumps({str(x): x for x in xrange(random.randint(min_size, max_size))})

times = []
for i in xrange(SAMPLES):
    start = time.time()
    cpu_bound()
    times.append(time.time()-start)


sns.set(style="white", palette="muted", color_codes=True)
sns.set_context("notebook", font_scale=1.5, rc={"lines.linewidth": 1.5})
f, axes = plt.subplots(2, 1, sharex=True)
sns.despine(left=True)

io = sns.distplot(wait_times, color='m', ax=axes[0], label='i/o bound request')
io.legend()
cpu = sns.distplot(times, color='b', ax=axes[1], label='cpu bound request')
cpu.legend()
axes[1].set_xlabel('response time (s)')

plt.setp(axes, yticks=[])
plt.tight_layout()

plt.show()
