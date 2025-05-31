import pyvisa
import time
import pandas as pd
import os
from datetime import datetime
from os.path import join
import numpy as np
import matplotlib.pyplot as plt

# ---

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

def generate_bipolar_square_wave(Vmax, n_cycles):
    """
    Generate a bipolar square wave of voltages.

    Parameters:
        Vmax (float): Maximum voltage value.
        n_cycles (int): Number of cycles of the waveform.

    Returns:
        numpy.ndarray: An array of the voltage values representing the bipolar square wave.
    """
    # Define one full cycle of the bipolar square wave
    single_cycle = [0, Vmax, 0, -Vmax, 0]

    # Repeat the single cycle 'n_cycles' times
    bipolar_wave = np.tile(single_cycle, n_cycles)

    return bipolar_wave


# ---
# inputs

# Keithley 6517b
GPIB = 27
BoardIndex = 0

# SOURCING
Vo, Vmax, dV = 0, -500, -100
V_ramp_up = np.arange(Vo, Vmax + Vmax / np.abs(Vmax), dV)
Vs = append_reverse(arr=V_ramp_up, single_point_max=True)
#Vs = generate_bipolar_square_wave(Vmax, n_cycles=10)

# Define one full cycle of the bipolar square wave
Vmax = 100
# Vs = np.ones(100) * Vmax
# single_cycle = [0, 0, 0, 0, 0, 0, 0, 0, Vmax, Vmax, Vmax, Vmax, Vmax, Vmax, Vmax, Vmax]
single_cycle = [Vmax, Vmax, Vmax, Vmax, Vmax, Vmax, Vmax, Vmax,
                -Vmax, -Vmax, -Vmax, -Vmax, -Vmax, -Vmax, -Vmax, -Vmax]
Vs = np.tile(single_cycle, 6)
print(Vs)
# SENSING
Imax = 20e-9
NPLC = 10  # (default = 1) Set integration rate in line cycles (0.01 to 10)
elements_sense = 'READ,TST,VSO'  # Current, Timestamp, Voltage Source
idxC, idxT, idxV = 0, 1, 2
num_elements = len(elements_sense.split(','))

assm = '05312025_W13-A3_Pad-Only' # C18-30pT-25+10nmAu
tid = 21
path_results = join(r'C:\Users\nanolab\Desktop\sean\05312025_W13_Pads-Only\CurrentLeakage')
save_name = 'tid{}_A3_{}V_{}NPLC'.format(tid, Vmax, NPLC)
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
k3.timeout = 5 * 1000

# RESET to defaults
k3.write('*RST')

# SYSTEM
k3.write(':SYST:RNUM:RES')  # reset reading number to zero
k3.write(':SYST:ZCOR ON')   # Enable (ON) or disable (OFF) zero correct (default: OFF)
k3.write(':SYST:ZCH OFF')   # Enable (ON) or disable (OFF) zero check (default: OFF)
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

# Get current time
current_time = datetime.now()
time_started = current_time.strftime('%H:%M:%S')

# Execute configured measurement
k3.write('OUTP ON')         # Turn source ON
k3.write(':SYST:TST:REL:RES')   # Reset relative timestamp to zero seconds
k3.write(':INIT')           # Move from IDLE state to ARM Layer 1

data = []
for Vapp in Vs:
    k3.write(':SOUR:VOLT ' + str(Vapp))  # Set voltage level
    meas = k3.query_ascii_values(':FETCh?')
    print(meas)
    data.append(meas)

k3.write(':SOUR:VOLT 0')    # Set voltage level to 0
"""time.sleep(0.05)
k3.write(':SOUR:VOLT -5')    # Set voltage level to 0
time.sleep(0.05)
k3.write(':SOUR:VOLT 0')    # Set voltage level to 0
time.sleep(0.05)"""
k3.write(':OUTP OFF')       # turn output off
# k3.write('*RST')            # reset GPIB to default
k3.close()                  # close instrument

# ---

# ----------------------------------------------------------------------------------------------------------------------
# POST-PROCESSING

# reshape array
data_struct = np.reshape(data, (num_points, num_elements))
num_samples = len(data_struct[:, 1])
t_total = data_struct[-1, 1] - data_struct[0, 1]
ramp_rate = Vmax / (t_total / 2)
sampling_rate = t_total / num_samples
sampling_freq = 1 / sampling_rate

print("--- Actual:")
print("Voltage ramp rate: {} V/s".format(np.round(ramp_rate, 2)))
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
    print("detected -V")
t_rise, t_fall = t[:idx_split + 1], t[idx_split:]
V_rise, V_fall = V[:idx_split + 1], V[idx_split:]
I_rise, I_fall = I[:idx_split + 1], I[idx_split:]

# plot
fig, (ax1, ax2) = plt.subplots(nrows=2, sharex=True, gridspec_kw={'height_ratios': [1, 2]})

ax1.plot(t_rise, V_rise, '-o', color='r', label='Rising')
ax1.plot(t_fall, V_fall, '-o', color='b', label='Falling')
# ax1.set_xlabel('TSTamp (s)')
ax1.set_ylabel('VOLTage (V)')
ax1.legend(title='smpl rate={} ms'.format(int(np.round(sampling_rate * 1e3, 0))))

ax2.plot(t_rise, I_rise, '-o', color='r')
ax2.plot(t_fall, I_fall, '-o', color='b')
# ax2.set_xlabel('VOLTage (V)')
ax2.set_xlabel('TSTamp (s)')
ax2.set_ylabel('CURRent (nA)')
ax2.grid(alpha=0.25)

ax1.set_title(plot_title + '\n' + "Voltage ramp rate: {} V/s".format(np.round(ramp_rate, 2)))
current_time = datetime.now()
time_finished = current_time.strftime('%H:%M:%S')
plt.suptitle(f'5/28/2025: Time started: {time_started}, finished: {time_finished}', fontsize=10)

plt.tight_layout()
if save_:
    plt.savefig(join(path_results, save_name + '.png'), dpi=300)
plt.show()
plt.close()

# --- export to excel
if save_:
    df = pd.DataFrame(data_struct, columns=['V', 'I', 't'])
    df.to_excel(join(path_results, save_name + '.xlsx'))
