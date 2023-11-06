from os.path import join
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

read_dir = r'C:\Users\nanolab\Desktop\instrumentControl\LabSmith HVS448\test floating voltage difference\10dV'

files = [f for f in os.listdir(read_dir) if f.endswith('.trc')]

fig, (ax1, ax2) = plt.subplots(nrows=2, sharex=True, figsize=(7, 5))
px, py = 'time (s)', 'dV'

for f in files:
    df = pd.read_csv(join(read_dir, f), delimiter=r'\t', engine='python')

    dff = df[df['Step number'] == 1]
    dff = dff.iloc[1:]

    # normalize time
    dff[px] = dff[px] - dff[px].iloc[0]

    # get voltage difference
    dff[py] = dff['Ch. A Voltage (V)'] - dff['Ch. C Voltage (V)']

    ax1.plot(dff[px], dff[py], '-o',
             label='{}: {}'.format(f[-8:-4], np.round(dff[py].std(), 2)))
    ax2.plot(dff[px], dff[py] / dff[py].mean(), '-o',
             label='{}: {}'.format(f[-8:-4], np.round(dff[py].std() / dff[py].mean(), 2)))


ax1.set_ylabel('dV')
ax1.legend(loc='upper left', bbox_to_anchor=(1, 1), title=r'$\Delta V: \: \sigma$')
ax1.grid(alpha=0.5)

ax2.set_xlabel(px)
ax2.set_ylabel('norm dV')
ax2.grid(alpha=0.5)
ax2.legend(loc='upper left', bbox_to_anchor=(1, 1), title=r'$\Delta V: \: \sigma/\mu$')

plt.tight_layout()
plt.savefig(join(read_dir, 'results_dV=50V.png'))
plt.show()

