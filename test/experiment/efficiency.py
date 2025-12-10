# data from https://allisonhorst.github.io/palmerpenguins/

import matplotlib.pyplot as plt
import numpy as np

species = ("k=1", "k=2", "k=3", "k=4")
penguin_means = {
#    'baseline': (6.9, 95.1, 253.8, 453.0),
#    'ours': (6.9, 77.4, 167.7, 215.9),
#	 'baseline': (2.8, 498.1, 2822.0, 10992.1),
#	 'ours': (2, 221.1, 856.4, 1939.5),
#	 'baseline': (2.7, 478.7, 2196.9, 6724.3),
#	 'ours': (2.1, 227.2, 986.0, 2796.0),
	 'baseline': (4.3, 770.4, 2786.5, 8468.7),
	 'ours': (3.4, 525.8, 1355.4, 2827.3),
}

x = np.arange(len(species))  # the label locations
width = 0.3  # the width of the bars
multiplier = 0

fig, ax = plt.subplots(layout='constrained')

for attribute, measurement in penguin_means.items():
    offset = width * multiplier
    rects = ax.bar(x + offset, measurement, width, label=attribute)
    ax.bar_label(rects, padding=3)
    multiplier += 1

# Add some text for labels, title and custom x-axis tick labels, etc.
ax.set_ylabel('time consumption (secs)')
#ax.set_title('Penguin attributes by species')
ax.set_xticks(x + width, species)
ax.legend(loc='upper left')
ax.set_ylim(0, 10000)

plt.show()
