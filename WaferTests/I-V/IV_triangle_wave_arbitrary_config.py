from os.path import join
import pyvisa
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


""" Description of this code

test 1
1 cycle: 0 V to 100 V to -100 V to 0 V over 4 seconds (0.5 Hz)

test 2
5 cycles: 0 V to 100 V to -100 V to 0 V over 2 seconds (1 Hz)


Inputs:
1. peak voltage (e.g., 100 V)
2. pm (+V to -V) or pp (+V to 0)
3. frequency (e.g., 0.5 Hz or 1 Hz)
"""

# --- FUNCTION FOR CONVERTING NUMPY ARRAY TO STRING LIST FOR KEITHLEY

def append_reverse(arr, single_point_max):
    """
    Append a NumPy array to itself in reverse order.
    """
    reversed_arr = arr[::-1]

    if single_point_max is True:
        reversed_arr = reversed_arr[1:]

    appended_arr = np.concatenate((arr, reversed_arr))

    return appended_arr

def numpy_array_to_string(arr):
    # Convert the NumPy array elements to strings
    str_arr = arr.astype(str)

    # Join the string elements with commas
    joined_str = ','.join(str_arr)

    return joined_str


# --- VARIABLES THAT RARELY CHANGE
GPIB = 27

# --- KEITHLEY CODE
"""
Inputs:
1. peak voltage (e.g., 100 V)
2. pm (+V to -V) or pp (+V to 0)
3. frequency (e.g., 0.5 Hz or 1 Hz)
"""

# RANGE
start, stop = 0, 100
step = stop / 5
values = np.arange(start, stop + step, step)
values_up_and_down = append_reverse(values, single_point_max=True)
values_lst = numpy_array_to_string(values_up_and_down)
num_points = len(values_up_and_down)

current_range = 110E-6

# FREQUENCY
source_measure_delay = 0.025  #0.015 (s)             0.01: 1.8 s half-period (i.e., 0-peak-0 V)
NPLC = 0.5  # (Number of Power Line Cycles)
integration_period = NPLC / 60

# TODO: Set the voltage to 0V at the end of the test, OR, need to do something to remove all charge from system.
path_results = r'C:\Users\nanolab\Desktop\sean\test_keithley'
save_name = 'W00x_0V_test00_'
plot_title = 'W00x: source measure delay={} s, NPLC={}'.format(source_measure_delay, NPLC)

# DATA TYPES
elements_sense = 'VOLTage, CURRent, TIME'  #, RESistance, STATus
idxV, idxC, idxT, idxR, idxSTAT = 0, 1, 2, 3, 4
num_elements = len(elements_sense.split(','))

# ---

rm = pyvisa.ResourceManager()
keithley = rm.open_resource("GPIB::{}".format(GPIB))

# 0.
keithley.write('*RST')  # Restore GPIB default

keithley.write(':FORMat:ELEMents:SENSe ' + elements_sense)
keithley.write(':DATA:TSTamp:FORMat DELTa')

# keithley.write(':SENS:FUNC:CONC OFF')  # Turn off concurrent functions.
keithley.write(':SOUR:FUNC VOLT')  # Volts source function.
keithley.write(':SOUR:VOLT:RANG MAX')  # Select V-source range (n = range).
keithley.write(':SENS:FUNC "CURR:DC"')  # Current sense function.
keithley.write(':SENS:CURR:PROT %g' % current_range)  # 1 mA current compliance.
keithley.write(':SENS:CURR:RANG %g' % current_range)  # 1 mA current compliance.
keithley.write(':SENS:CURR:NPLC %g' % NPLC)  # Specify integration rate (in line cycles): [0.01 to 10E3] (default = 1)


keithley.write(':SOUR:VOLT:MODE LIST')  # List volts sweep mode.
keithley.write(':SOUR:LIST:VOLT ' + values_lst)  # List sweep points.
keithley.write(':TRIG:COUN ' + str(num_points))  # Trigger count = # sweep points.
keithley.write(':SOUR:DEL %g' % source_measure_delay)  # 50ms source delay.

keithley.write(':OUTP ON')  # Turn on source output.
data = keithley.query_ascii_values(':READ?', container=np.array)  # Trigger sweep, request data.

""" Custom sweep commands

:SOURce:VOLTage:MODE LIST               Select voltage list (custom) sweep mode.
:SOURce:LIST:VOLTage < list>            Define V-source list (list = V1, V2,... Vn).
:SOURce:LIST:VOLTage:APPend <list>      Add V-source list value(s) (list =V1, V2,...Vn).
:SOURce:LIST:VOLTage:POINts?            Query length of V-source list.
:SOURce:SWEep:RANGing <name>            Select source ranging (name = BEST, AUTO, or FIXed).
"""

# Sean Code

# --- POST-PROCESSING

data_elements = keithley.query(':FORMat:ELEMents:SENSe?')
keithley.write(':OUTP OFF')  # End example given in manual

# Data analysis

print("Data Elements " + data_elements)
data_struct = np.reshape(data, (num_points, num_elements))

sampling_rate = np.round((data_struct[-1, idxT] - data_struct[0, idxT]) / len(data_struct[:, idxT]), 5)
print("Sampling Rate: {}".format(np.round(sampling_rate, 4)))
print("Time to sample 100 points: {}".format(np.round(sampling_rate * 100, 3)))
print("Time to sample 500 points: {}".format(np.round(sampling_rate * 500, 3)))

# ---

# - PLOTTING

# arrays to plot
t = data_struct[:, idxT] - data_struct[0, idxT]  # convert to relative time since start
V = data_struct[:, idxV]
I = data_struct[:, idxC] * 1e9  # convert to nano Amps

# split into rising/falling traces
idx_split = np.argmax(V) + 1
t_rise, t_fall = t[:idx_split], t[idx_split:]
V_rise, V_fall = V[:idx_split], V[idx_split:]
I_rise, I_fall = I[:idx_split], I[idx_split:]


fig, (ax1, ax2) = plt.subplots(nrows=2, gridspec_kw={'height_ratios': [1, 1]})

ax1.plot(t_rise, V_rise, '-o', color='r', label='Rising')
ax1.plot(t_fall, V_fall, '-o', color='b', label='Falling')
ax1.set_xlabel('TSTamp (s)')
ax1.set_ylabel('VOLTage (V)')
ax1.legend(title='sampling rate={} (#/s)'.format(np.round(sampling_rate, 3)))

ax2.plot(V_rise, I_rise, '-o', color='r')
ax2.plot(V_fall, I_fall, '-o', color='b')
ax2.set_xlabel('VOLTage (V)')
ax2.set_ylabel('CURRent (nA)')

plt.suptitle(plot_title)
plt.tight_layout()
# plt.savefig(join(path_results, save_name + '.png'), dpi=300)
plt.show()
plt.close()

# --- export to excel

# df = pd.DataFrame(data_struct, columns=['V', 'I', 't'])
# df.to_excel(join(path_results, save_name + '.xlsx'))
