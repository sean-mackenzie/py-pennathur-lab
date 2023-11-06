import pyvisa
import time
import pandas as pd
import os
from os.path import join
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

# ---

def fit_line(x, a, b):
    return a * x + b

def append_reverse(arr, single_point_max):
    """
    Append a NumPy array to itself in reverse order.
    """
    reversed_arr = arr[::-1]

    if single_point_max is True:
        reversed_arr = reversed_arr[1:]

    appended_arr = np.concatenate((arr, reversed_arr))

    return appended_arr

def if_not_create(filepath):
    if not os.path.exists(filepath):
        os.makedirs(filepath)

# ---
# inputs

# Keithley 6517b
GPIB = 27
BoardIndex = 2

# SOURCING
Vo, Vmax, dV = 0, 300, 25
num_cycles = 10
V_ramp_up = np.arange(Vo, Vmax + Vmax / np.abs(Vmax) * 0.5, dV)
Vs = append_reverse(arr=V_ramp_up, single_point_max=True)
Vs = np.concatenate((Vs, Vs * -1))  # fit line to +/-V-I curve.
print(Vs)
# SENSING
Imax = 1e-6  # NOTE: if CURRent RANGe is too high, then you will measure a relatively large bias current (e.g., -220 nA for 1mA range)
NPLC = 0.1  # (default = 1) Set integration rate in line cycles (0.01 to 10)
elements_sense = 'READ,TST,VSO'  # Current, Timestamp, Voltage Source
idxC, idxT, idxV = 0, 1, 2
num_elements = len(elements_sense.split(','))

assm = 'w18'
path_results = r'C:\Users\nanolab\Desktop\sean\PASSM5\Keithley6517b_Etest'
save_name = '{}_{}Vramp-{}Cycles_VC11'.format(assm, Vmax, num_cycles)
plot_title = '{}: Keithley 6517b, NPLC={}'.format(assm, NPLC)

save_ = True
if save_:
    if_not_create(path_results)

# ----------------------------------------------------------------------------------------------------------------------

num_points = len(Vs)
sampling_period = NPLC / 60

print("Theoretical:")
print("Sampling period: {} ms".format(np.round(sampling_period * 1e3, 2)))
print("Min. total sampling time ({} samples): {} s".format(num_points, np.round(sampling_period * num_points, 3)))

# ----------------------------------------------------------------------------------------------------------------------
# RUN MEASUREMENT

# open instrument
rm = pyvisa.ResourceManager()
k3 = rm.open_resource('GPIB{}::{}::INSTR'.format(BoardIndex, GPIB))

# RESET to defaults
k3.write('*RST')

# NOTE: if ZCH OFF is not explicitly sent to Keithley, then no current will be measured.
k3.write(':SYST:ZCH OFF')   # Enable (ON) or disable (OFF) zero check (default: OFF)

# SYSTEM
k3.write(':SYST:RNUM:RES')  # reset reading number to zero
k3.write(':SYST:ZCOR ON')   # Enable (ON) or disable (OFF) zero correct (default: OFF)
k3.write(':DISP:ENAB ON')   # Enable or disable the front-panel display
k3.write(':SYST:TSC OFF')    # Enable or disable external temperature readings (default: ON)
k3.write(':SYST:TST:TYPE REL')  # Configure timestamp type: RELative or RTClock
k3.write(':TRAC:FEED:CONT NEV')  # disable buffer control
k3.write(':FORM:DATA ASCii')  # Select data format: ASCii, REAL, SREal, DREal
k3.write(':FORM:ELEM READ,TST,VSO')  # data elements: VSOurce, READing, CHANnel, RNUMber, UNITs, TSTamp, STATus, ETEM, HUM

# --- Define Trigger Model
k3.write(':INIT:CONT OFF')       # When instrument returns to IDLE layer, CONTINUOUS ON = repeat; OFF = hold in IDLE

k3.write(':ARM:TCON:DIR ACCeptor')        # Wait for Arm Event (default: ACCeptor)
k3.write(':ARM:COUN 1')                   # Specify arm count: number of cycles around arm layer (default: 1)
k3.write(':ARM:SOUR IMM')                 # Select control source: IMM, TLINk or EXT. (default: IMM)
# k3.write(':ARM:LAYer1:TCON:ASYN:ILIN 1')    # Input line for asynchronous trigger (default: 2)
# k3.write(':ARM:LAYer1:TCON:ASYN:OLIN 2')    # Output line for asynchronous trigger (default: 1)

k3.write(':ARM:LAYer2:TCON:DIR ACCeptor')   # Wait for Arm Event
k3.write(':ARM:LAYer2:COUN ' + str(num_cycles))              # Perform 1 arm layer cycle
k3.write(':ARM:LAYer2:SOUR IMM')            # Immediately go to Arm Layer 2
# k3.write(':ARM:LAYer2:TCON:ASYN:ILIN 1')    # Input line for asynchronous trigger (default: 2)
# k3.write(':ARM:LAYer2:TCON:ASYN:OLIN 2')    # Output line for asynchronous trigger (default: 1)
k3.write(':ARM:LAYer2:DEL 0')               # After receiving Arm Layer 2 Event, delay before going to Trigger Layer

k3.write(':TRIG:TCON:DIR ACC')     # Wait for trigger event (TLINK)
k3.write(':TRIG:COUN ' + str(num_points))   # Set measure count (1 to 99999 or INF) (preset: INF; Reset: 1)
k3.write(':TRIG:SOUR IMM')             # Select control source (HOLD, IMMediate, TIMer, MANual, BUS, TLINk, EXTernal) (default: IMM)
# k3.write(':TRIG:TCON:PROT ASYN')        # ASYN = use separate trigger lines, SSYN = input/output use same trigger lines
# k3.write(':TRIG:TCON:ASYN:ILIN 1')    # Input line for asynchronous trigger (default: 2)
# k3.write(':TRIG:TCON:ASYN:OLIN 2')    # Output line for asynchronous trigger (default: 1)
k3.write(':TRIG:DEL 0')                  # After receiving Measure Event, delay before Device Action

# Set up Source functions
print(k3.query(':SOUR:VOLT:MCON?'))
k3.write(':SOUR:VOLT:MCON ON')      # Enable voltage source LO to ammeter LO connection (SVMI)  (default: OFF)
print(k3.query(':SOUR:VOLT:MCON?'))
k3.write(':SOUR:VOLT 0')            # Define voltage level: -1000 to +1000 V (default: 0)
k3.write(':SOUR:VOLT:RANG ' + str(np.abs(Vmax)))     # Define voltage range: <= 100: 100V, >100: 1000 V range (default: 100 V)
k3.write(':SOUR:VOLT:LIM 1000')     # Define voltage limit: 0 to 1000 V (default: 1000 V)

# Set up Sense functions
k3.write(':SENS:FUNC "CURR"')               # 'VOLTage[:DC]', 'CURRent[:DC]', 'RESistance', 'CHARge' (default='VOLT:DC')
# k3.write(':SENS:CURR:APERture <n>')       # (default: 60 Hz = 16.67 ms) Set integration rate in seconds: 167e-6 to 200e-3
k3.write(':SENS:CURR:NPLC ' + str(NPLC))       # (default = 1) Set integration rate in line cycles (0.01 to 10)
k3.write(':SENS:CURR:RANG:AUTO OFF')        # Enable (ON) or disable (OFF) autorange
k3.write(':SENS:CURR:RANG ' + str(Imax))          # Select current range: 0 to 20e-3 (default = 20e-3)
k3.write(':SENS:CURR:REF 0')                # Specify reference: -20e-3 to 20e-3) (default: 0)
k3.write(':SENS:CURR:DIG 6')                # Specify measurement resolution: 4 to 7 (default: 6)

# Execute configured measurement
k3.write('OUTP ON')         # Turn source ON
k3.write(':SYST:TST:REL:RES')   # Reset relative timestamp to zero seconds
k3.write(':INIT')           # Move from IDLE state to ARM Layer 1

data = []
for cycle_i in range(num_cycles):
    for Vapp in Vs:
        k3.write(':SOUR:VOLT ' + str(Vapp))  # Set voltage level
        data.append(k3.query_ascii_values(':FETCh?'))

k3.write(':SOUR:VOLT 0')    # Set voltage level to 0
k3.write(':OUTP OFF')       # turn output off
k3.close()                  # close instrument

# ---

# ----------------------------------------------------------------------------------------------------------------------
# POST-PROCESSING

# reshape array
data_struct = np.reshape(data, (num_points * num_cycles, num_elements))
num_samples = len(data_struct[:, 1])
t_total = data_struct[-1, 1] - data_struct[0, 1]
sampling_rate = t_total / num_samples
sampling_freq = 1 / sampling_rate

print("--- Actual:")
print("Sampling rate: {} ms".format(np.round(sampling_rate * 1e3, 2)))
print("Sampling frequency: {} Hz".format(np.round(sampling_freq, 1)))
print("Min. total sampling time ({} samples): {} s".format(num_samples, np.round(t_total, 3)))

# ---

# - PLOTTING

# arrays to plot
t = data_struct[:, idxT] - data_struct[0, idxT]  # convert to relative time since start
V = data_struct[:, idxV]
I = data_struct[:, idxC] * 1e9  # convert to nano Amps

# plot
fig, (ax1, ax2) = plt.subplots(nrows=2, gridspec_kw={'height_ratios': [1, 2]})

# split data between cycles
for i in range(num_cycles):
    tc = t[i * num_points:(i + 1) * num_points]
    Vc = V[i * num_points:(i + 1) * num_points]
    Ic = I[i * num_points:(i + 1) * num_points]

    if Vmax > 0:
        Imax = np.max(Ic)
    else:
        Imax = np.min(Ic)

    ax1.plot(tc, Vc, '-o')
    ax2.plot(Vc, Ic, '-o', linewidth=0.5, label=np.round(Imax, 2))

ax1.set_xlabel('TSTamp (s)')
ax1.set_ylabel('VOLTage (V)')

ax2.set_xlabel('VOLTage (V)')
ax2.set_ylabel('CURRent (nA)')
ax2.grid(alpha=0.25)
ax2.legend(loc='upper left', bbox_to_anchor=(1, 1), title=r'$I_{max}$')

plt.suptitle(plot_title + ', smpl rate: {} ms'.format(int(np.round(sampling_rate * 1e3, 0))))
plt.tight_layout()
if save_:
    plt.savefig(join(path_results, save_name + '.png'), dpi=300)
plt.show()
plt.close()

# --- export to excel
if save_:
    df = pd.DataFrame(data_struct, columns=['V', 'I', 't'])
    df.to_excel(join(path_results, save_name + '.xlsx'))
