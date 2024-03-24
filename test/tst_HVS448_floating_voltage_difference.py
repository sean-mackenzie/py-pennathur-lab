from os.path import join
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# --- read files
read_dir = r'C:\Users\nanolab\Desktop\sean\instrumentControl\LabSmith HVS448\test floating voltage difference with shunt resistor - 3 channels\OOO_CCC_ASSM'

files = [f for f in os.listdir(read_dir) if f.endswith('.trc')]
file_ids = [int(f[-9:-5]) for f in files]

# ---

# --- Setup data processing and plotting

px = 'time (s)'  # column: time (should always remain the same)
skip_num = 0  # number of initial data points to skip (due to RC time constant, for example)
transient_num = None  # if measuring transients, only include up to this number of data points
step_num = 1  # column: Step Number (Step Number should equal whichever step had Vapp)
step_nums = [1, 2, 3, 4]
ch_active = 'Ch. A Voltage (V)'  # the column that you want to plot (e.g., 'Ch. A Voltage (V)')
ch_ground = 'Ch. D Voltage (V)'  # the column that was grounded (e.g., 'Ch. D Voltage (V)')

py1 = ch_active
py = 'dV'  # column name of the difference between the active and grounded channels

fig, (ax1, ax2, ax3, ax4) = plt.subplots(nrows=4, sharex=True, figsize=(10, 7))
ms = 1
lw=0.5

""" TWO OPTIONS:
        1. Multiple .trc files comparing a single channel (e.g., Channel A)
        2. A single .trc file comparing multiple channels (e.g., Channels A, B, C)
"""

if len(files) == 1:
    ch_ground = 'Ch. D Voltage (V)'
    chs = ['A', 'B', 'C']

    f = files[0]
    fid = file_ids[0]

    df = pd.read_csv(join(read_dir, f), delimiter=r'\t', engine='python')

    if step_nums is not None:
        dff = df[df['Step number'].isin(step_nums)]
    else:
        dff = df[df['Step number'] == step_num]

    if transient_num is not None:
        dff = dff.iloc[:transient_num]
    else:
        dff = dff.iloc[skip_num:]

    # normalize time
    dff[px] = dff[px] - dff[px].iloc[0]

    for ch in chs:
        ch_active = 'Ch. {} Voltage (V)'.format(ch)
        py1 = 'Ch. {} Voltage (V)'.format(ch)
        py = 'Ch{}_dV'.format(ch)  # column name of the difference between the active and grounded channels

        # get voltage difference
        dff[py] = dff[ch_active] - dff[ch_ground]

        # --- Plot Active Channel Voltage: absolute and normalized
        ax1.plot(dff[px], dff[py1],  # - fid, # - fid,
                 '-o', ms=ms, lw=lw,
                 label='Ch{}: {}'.format(ch, np.round(dff[py1].std(), 2)))
        ax2.plot(dff[px], (dff[py1] - dff[py1].mean()) / dff[py1].mean(), 'o', ms=ms,
                 label='Ch{}: {}'.format(ch, np.round(dff[py1].std() / dff[py1].abs().mean() * 100, 1)))

        # --- Plot Voltage Difference Between Active and Ground Channels: absolute and normalized
        ax3.plot(dff[px], dff[py],  # - fid,  # - fid,
                 '-o', ms=ms, lw=lw,
                 label='Ch{}: {}'.format(ch, np.round(dff[py].std(), 2)))
        ax4.plot(dff[px], (dff[py] - dff[py].mean()) / dff[py].mean(), 'o', ms=ms,
                 label='Ch{}: {}'.format(ch, np.round(dff[py].std() / dff[py].abs().mean() * 100, 1)))

    ax1.set_ylabel(r'$V_{active}$')  # - V_{target}
    ax1.legend(loc='upper left', bbox_to_anchor=(1, 1), title=r'$\sigma \: (V)$')
    ax1.grid(alpha=0.5)

    ax2.set_ylabel(r'$V_{active}/\overline{V_{active}}$')
    ax2.grid(alpha=0.5)
    ax2.legend(loc='upper left', bbox_to_anchor=(1, 1), title=r'$\sigma/\mu \: (\%)$')

    ax3.set_ylabel(r'$\left(V_{active}-V_{GND}\right)$')  # - V_{target}
    ax3.legend(loc='upper left', bbox_to_anchor=(1, 1), title=r'$\Delta V: \: \sigma \: (V)$')
    ax3.grid(alpha=0.5)

    ax4.set_xlabel(px)
    ax4.set_ylabel(r'$\Delta dV/\overline{dV} (\%)$')
    ax4.grid(alpha=0.5)
    ax4.legend(loc='upper left', bbox_to_anchor=(1, 1), title=r'$\Delta V: \: \sigma/\mu \: (\%)$')

    plt.tight_layout()
    plt.savefig(join(read_dir, 'results_{}V_absolute.png'.format(fid)), dpi=300)
    plt.show()
    plt.close()

    # ---

    fig, (ax1, ax2) = plt.subplots(nrows=2, sharex=True, figsize=(8, 5))

    for ch in chs:
        ch_active = 'Ch. {} Voltage (V)'.format(ch)
        py1 = 'Ch. {} Voltage (V)'.format(ch)
        py2 = 'Ch. {} Current (uA)'.format(ch)

        # --- Plot Active Channel Voltage: absolute and normalized
        ax1.plot(dff[px], dff[py1], '-o', ms=ms, lw=lw, label='{}'.format(ch))
        ax2.plot(dff[px], dff[py2], '-o', ms=ms, lw=lw, label='{}'.format(ch))

    ax1.set_ylabel(r'$V_{i} \: (V) $')  # - V_{target}
    ax1.legend(loc='upper left', bbox_to_anchor=(1, 1), title='Channel')
    ax1.grid(alpha=0.5)

    ax2.set_ylabel(r'$I_{i} \: (\mu A)$')
    ax2.grid(alpha=0.5)
    ax2.legend(loc='upper left', bbox_to_anchor=(1, 1), title='Channel')

    plt.tight_layout()
    plt.savefig(join(read_dir, 'results_{}V_absolute_I-V.png'.format(fid)), dpi=300)
    plt.show()
    plt.close()


else:
    for f, fid in zip(files, file_ids):

        df = pd.read_csv(join(read_dir, f), delimiter=r'\t', engine='python')

        dff = df[df['Step number'] == step_num]

        if transient_num is not None:
            dff = dff.iloc[:transient_num]
        else:
            dff = dff.iloc[skip_num:]

        # normalize time
        dff[px] = dff[px] - dff[px].iloc[0]

        # get voltage difference
        dff[py] = dff[ch_active] - dff[ch_ground]

        # --- Plot Active Channel Voltage: absolute and normalized
        ax1.plot(dff[px], dff[py1], # - fid, # - fid,
                 '-o', ms=ms, lw=lw,
                 label='{}V: {}'.format(fid, np.round(dff[py1].std(), 2)))
        ax2.plot(dff[px], (dff[py1] - dff[py1].mean()) / dff[py1].mean(), 'o', ms=ms,
                 label='{}V: {}'.format(fid, np.round(dff[py1].std() / dff[py1].abs().mean() * 100, 1)))

        # --- Plot Voltage Difference Between Active and Ground Channels: absolute and normalized
        ax3.plot(dff[px], dff[py], # - fid,  # - fid,
                 '-o', ms=ms, lw=lw,
                 label='{}V: {}'.format(fid, np.round(dff[py].std(), 2)))
        ax4.plot(dff[px], (dff[py] - dff[py].mean()) / dff[py].mean(), 'o', ms=ms,
                 label='{}V: {}'.format(fid, np.round(dff[py].std() / dff[py].abs().mean() * 100, 1)))


    ax1.set_ylabel(r'$V_{active}$')  #  - V_{target}
    ax1.legend(loc='upper left', bbox_to_anchor=(1, 1), title=r'$\sigma \: (V)$')
    ax1.grid(alpha=0.5)

    ax2.set_ylabel(r'$V_{active}/\overline{V_{active}}$')
    ax2.grid(alpha=0.5)
    ax2.legend(loc='upper left', bbox_to_anchor=(1, 1), title=r'$\sigma/\mu \: (\%)$')

    ax3.set_ylabel(r'$\left(V_{active}-V_{GND}\right)$')  #  - V_{target}
    ax3.legend(loc='upper left', bbox_to_anchor=(1, 1), title=r'$\Delta V: \: \sigma \: (V)$')
    ax3.grid(alpha=0.5)

    ax4.set_xlabel(px)
    ax4.set_ylabel(r'$\Delta dV/\overline{dV} (\%)$')
    ax4.grid(alpha=0.5)
    ax4.legend(loc='upper left', bbox_to_anchor=(1, 1), title=r'$\Delta V: \: \sigma/\mu \: (\%)$')

    plt.tight_layout()
    plt.savefig(join(read_dir, 'results_absolute.png'), dpi=300)
    plt.show()
    plt.close()
