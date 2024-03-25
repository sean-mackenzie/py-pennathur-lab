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
BoardIndex = 0

# SOURCING
Vo, Vmax, dV = 0, 35, 5
V_ramp_up = np.arange(Vo, Vmax + Vmax / np.abs(Vmax) * 0.5, dV)
Vs = append_reverse(arr=V_ramp_up, single_point_max=True)
# Vs = np.concatenate((Vs, Vs * -1))  # fit line to +/-V-I curve.
print(Vs)
# SENSING
Imax = 1e-6  # NOTE: if CURRent RANGe is too high, then you will measure a relatively large bias current (e.g., -220 nA for 1mA range)
NPLC = 2  # (default = 1) Set integration rate in line cycles (0.01 to 10)
elements_sense = 'READ,TST,VSO'  # Current, Timestamp, Voltage Source
idxC, idxT, idxV = 0, 1, 2
num_elements = len(elements_sense.split(','))

# dx = 100, 300, 500
# dia = {100: bottom=10, middle=15, top=25}
#       {300: bottom=30, middle=45, top=60}
#       {500: bottom=50, middle=75, top=100}
# device_id: bottom=1, middle=2, top=3

wafer = 'W2_2umOx'
memb = 'MBD2'
assm = 'W2'
dx = 500
dia = 100
device_id = 2
run_number = 2

path_results = r'C:\Users\nanolab\Desktop\sean\microposts\{}_{}'.format(wafer, memb)
path_results = join(path_results, 'dx{}_dia{}_n{}'.format(dx, dia, device_id))

save_name = '{}_{}Vsweep_dx{}_dia{}_n{}_run{}'.format(assm, Vmax, dx, dia, device_id, run_number)
plot_title = 'W, DX, DIA, N, Run = ({}, {}, {}, {})'.format(assm, dx, dia, device_id, run_number)

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
k3.write(':ARM:LAYer2:COUN 1')              # Perform 1 arm layer cycle
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
data_struct = np.reshape(data, (num_points, num_elements))
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

# split into rising/falling traces
if Vmax > 0:
    idx_split = np.argmax(V)
else:
    idx_split = np.argmin(V)
t_rise, t_fall = t[:idx_split + 1], t[idx_split:]
V_rise, V_fall = V[:idx_split + 1], V[idx_split:]
I_rise, I_fall = I[:idx_split + 1], I[idx_split:]

# plot
fig, (ax1, ax2) = plt.subplots(nrows=2, gridspec_kw={'height_ratios': [1, 2]})

ax1.plot(t_rise, V_rise, '-o', color='r', label='Rising')
ax1.plot(t_fall, V_fall, '-o', color='b', label='Falling')
ax1.set_xlabel('TSTamp (s)')
ax1.set_ylabel('VOLTage (V)')
ax1.legend(title='smpl rate={} ms'.format(int(np.round(sampling_rate * 1e3, 0))))

ax2.plot(V_rise, I_rise, '-o', color='r')
ax2.plot(V_fall, I_fall, '-o', color='b')
ax2.set_xlabel('VOLTage (V)')
ax2.set_ylabel('CURRent (nA)')
ax2.grid(alpha=0.25)

fit_I_V = False
if fit_I_V:
    V_pos, V_neg = V[V > 0], V[V < 0]
    I_pos, I_neg = I[V > 0], I[V < 0]

    for xd, yd, lbl, clr in zip([V_pos, V_neg], [I_pos, I_neg], ['+V', '-V'], ['r', 'b']):
        popt, pcov = curve_fit(fit_line, xd, yd)
        slope, intercept = popt
        resistance = 1 / slope * 1e6  # account for micro Amps
        ax2.plot(xd, fit_line(xd, *popt), '-', linewidth=1.5, color=clr,
                 label='{}: '.format(lbl) + r'$\Omega = $' + '{} kOhms'.format(np.round(resistance * 1e-3, 2)))
    ax2.legend(loc='upper left')

plt.suptitle(plot_title)
plt.tight_layout()
if save_:
    plt.savefig(join(path_results, save_name + '.png'), dpi=300)
plt.show()
plt.close()

# --- export to excel
if save_:
    df = pd.DataFrame(data_struct, columns=['V', 'I', 't'])
    df.to_excel(join(path_results, save_name + '.xlsx'))
