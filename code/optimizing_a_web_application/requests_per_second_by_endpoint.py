import matplotlib
matplotlib.use('QT4Agg')
import seaborn as sns
from matplotlib import pylab as plt

sns.set(style="white", palette="muted", color_codes=True)
sns.set_context("notebook", font_scale=1.5, rc={"lines.linewidth": 1.5})
f, ax = plt.subplots()
sns.despine()

sns.barplot(['i/o and cpu bound mix', 'i/o bound', 'cpu bound'], [60.59, 11.17, 545.44])
ax.set_ylabel('Requests per second (higher is better)')

plt.show()
