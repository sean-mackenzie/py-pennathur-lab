import pyvisa
import numpy as np
from os.path import join

GPIB = 23

# RANGE
start, stop, step = 0, 100, 10
values = np.arange(start, stop + step, step)
num_points = len(values)

current_range = 110E-6

# FREQUENCY
source_measure_delay = 0.005  # (s) 0.015
NPLC = 0.25  # (Number of Power Line Cycles)
integration_period = NPLC / 60

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

# keithley.write(':SENS:FUNC:CONC OFF')  # Turn off concurrent functions.  --> Doesn't seem to do anything
keithley.write(':SOUR:FUNC VOLT')  # Voltage source function.
keithley.write(':SOUR:VOLT:RANG MAX')  # Select V-source range (n = range).
keithley.write(':SENS:FUNC "CURR:DC"')  # Current sense function.
keithley.write(':SENS:CURR:PROT %g' % current_range)  # 1 mA current compliance.
keithley.write(':SENS:CURR:RANG %g' % current_range)  # 1 mA current compliance.
keithley.write(':SENS:CURR:NPLC %g' % NPLC)  # Specify integration rate (in line cycles): [0.01 to 10E3] (default = 1)

print(keithley.query(':SOUR:VOLT:RANG:AUTO?'))
print(keithley.query_ascii_values(':SOURce:VOLTage:RANG?'))
print(keithley.query_ascii_values(':SOURce:VOLTage:PROTection?'))
print(keithley.query_ascii_values(':SENS:CURR:RANG?'))
print(keithley.query_ascii_values(':SENS:CURR:PROTection?'))
print(keithley.query(':SENS:FUNC:OFF?'))

keithley.write(':SOUR:VOLT:START %g' % start)  # min(X) start current.
keithley.write(':SOUR:VOLT:STOP %g' % stop)  # max(X) stop current.
keithley.write(':SOUR:VOLT:STEP %g' % step)  # dX step current.
keithley.write(':SOUR:VOLT:MODE SWE')  # Select current sweep mode.
keithley.write(':SOUR:SWE:SPAC LIN')  # Select linear staircase sweep.
keithley.write(':SOUR:SWE:RANG FIXed')  # Auto source ranging.
keithley.write(':TRIG:COUN ' + str(num_points))  # Trigger count = # sweep points.
# NOTE:
#       * For single sweep, trigger count should equal number of points in the sweep: Points = (Stop-Start)/Step + 1.
#       * You can use ':SOUR:SWE:POIN?' query to read the number of points.
keithley.write(':SOUR:DEL %g' % source_measure_delay)  # 50ms source delay.
keithley.write(':OUTP ON')  # Turn on source output.

datas = []
for direction in ['UP', 'DOWn']:
    keithley.write('SOUR:SWE:DIR ' + direction)
    data = keithley.query_ascii_values('READ?', container=np.array)  # Trigger sweep, request data.
    datas.append(data)

# --- POST-PROCESSING

data_elements = keithley.query(':FORMat:ELEMents:SENSe?')
keithley.write(':OUTP OFF')  # End example given in manual

print(np.shape(datas))
data = [item for sublist in datas for item in sublist]

# Data analysis

print("Data Elements " + data_elements)
data_struct = np.reshape(data, (num_points * 2, num_elements))

sampling_rate = np.round((data_struct[-1, idxT] - data_struct[0, idxT]) / len(data_struct[:, idxT]), 5)
print("Sampling Rate: {}".format(np.round(sampling_rate, 4)))
print("Time to sample 100 points: {}".format(np.round(sampling_rate * 100, 3)))
print("Time to sample 500 points: {}".format(np.round(sampling_rate * 500, 3)))

# -

import matplotlib.pyplot as plt
path_results = r'C:\Users\nanolab\PythonProjects\py-pennathur-lab\examples\darkroom\results'

fig, (ax1, ax2) = plt.subplots(nrows=2, gridspec_kw={'height_ratios': [1, 1]})

ax1.plot(data_struct[:, idxT] - data_struct[0, idxT], data_struct[:, idxV], '-o', label=np.round(sampling_rate, 3))
ax1.set_xlabel('TSTamp (s)')
ax1.set_ylabel('VOLTage (V)')
ax1.legend(title='(#/s)')

ax2.plot(data_struct[:, idxV], data_struct[:, idxC], '-o')
ax2.set_xlabel('VOLTage (V)')
ax2.set_ylabel('CURRent (A)')

plt.suptitle('External Loop: 2X( :SOUR:SWE: Staircase )')
plt.tight_layout()
plt.savefig(join(path_results, 'ex7_sean_staircase_sweep_up_and_down.png'), dpi=300)
plt.show()
plt.close()
