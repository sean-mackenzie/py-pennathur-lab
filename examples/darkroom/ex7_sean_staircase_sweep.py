import pyvisa
import numpy as np
from os.path import join

GPIB = 23

start, stop, step = 0, 10, 1
values = np.arange(start, stop + step, step)
num_points = len(values)

elements_sense = 'VOLTage, CURRent, RESistance, TIME'  #, STATus
num_elements = len(elements_sense.split(','))

# ---

rm = pyvisa.ResourceManager()
keithley = rm.open_resource("GPIB::{}".format(GPIB))

# 0.
keithley.write('*RST')  # Restore GPIB default

keithley.write(':FORMat:ELEMents:SENSe ' + elements_sense)
keithley.write(':DATA:TSTamp:FORMat DELTa')

keithley.write(':SENS:FUNC:CONC OFF')  # Turn off concurrent functions.
keithley.write(':SOUR:FUNC VOLT')  # Voltage source function.
keithley.write(':SENS:FUNC "CURR:DC"')  # Current sense function.
keithley.write(':SENS:CURR:PROT 1E-3')  # 1 mA current compliance.
keithley.write(':SOUR:VOLT:START %g' % start)  # min(X) start current.
keithley.write(':SOUR:VOLT:STOP %g' % stop)  # max(X) stop current.
keithley.write(':SOUR:VOLT:STEP %g' % step)  # dX step current.
keithley.write(':SOUR:VOLT:MODE SWE')  # Select current sweep mode.
keithley.write(':SOUR:SWE:RANG AUTO')  # Auto source ranging.
keithley.write(':SOUR:SWE:SPAC LIN')  # Select linear staircase sweep.
keithley.write(':TRIG:COUN ' + str(num_points))  # Trigger count = # sweep points.
# NOTE:
#       * For single sweep, trigger count should equal number of points in the sweep: Points = (Stop-Start)/Step + 1.
#       * You can use ':SOUR:SWE:POIN?' query to read the number of points.
keithley.write(':SOUR:DEL 0.1')  # 100ms source delay.
keithley.write(':OUTP ON')  # Turn on source output.
data = keithley.query_ascii_values(':READ?', container=np.array)  # Trigger sweep, request data.

""" Linear and log staircase sweep commands

:SOURce:CURRent:CENTer <n>      Specify sweep center current (n = current).
:SOURce:CURRent:SPAN <n>        Specify sweep span current (n = current).
:SOURce:VOLTage:CENTer <n>      Specify sweep center voltage (n = voltage).
:SOURce:VOLTage:SPAN <n>        Specify sweep span voltage (n = voltage).
:SOURce:SWEep:RANGing <name>    Select source ranging (name = BEST, AUTO, or FIXed).
:SOURce:SWEep:SPACing <name>    Select sweep scale (name = LINear or LOGarithmic).
:SOURce:SWEep:DIREction <name>  Set sweep direction. Name = UP (sweep start to stop) or DOWn (sweep stop to start).
:SOURce:SWEep:CABort <name>     Abort on compliance. Name = NEVer (disable), EARLy (start of SDM cycle), or LATE (end of SDM cycle).
"""

# Sean Code:

data_elements = keithley.query(':FORMat:ELEMents:SENSe?')
keithley.write(':OUTP OFF')  # End example given in manual

# Data analysis

print("Data Elements " + data_elements)
data_struct = np.reshape(data, (num_points, num_elements))

sampling_rate = np.round((data_struct[-1, 3] - data_struct[0, 3]) / len(data_struct[:, 3]), 5)
print("Sampling Rate: {}".format(np.round(sampling_rate, 4)))
print("Time to sample 100 points: {}".format(np.round(sampling_rate * 100, 3)))
print("Time to sample 500 points: {}".format(np.round(sampling_rate * 500, 3)))

# -

import matplotlib.pyplot as plt
path_results = r'C:\Users\nanolab\PythonProjects\py-pennathur-lab\examples\darkroom\results'

fig, (ax1, ax2) = plt.subplots(nrows=2, gridspec_kw={'height_ratios': [1, 3]})

ax1.plot(data_struct[:, 3] - data_struct[0, 3], data_struct[:, 1], '-o', label=np.round(sampling_rate, 3))
ax1.set_xlabel('TSTamp (s)')
ax1.set_ylabel('CURRent (A)')
ax1.legend(title='Sampling rate (s)')

ax2.plot(data_struct[:, 0], data_struct[:, 1], '-o', label='{:.2E}'.format(np.round(np.mean(data_struct[:, 2]), 1)))
ax2.set_xlabel('VOLTage (V)')
ax2.set_ylabel('CURRent (A)')
ax2.legend(title=r'$\overline{\Omega}}$')

plt.suptitle('Internal Process - :SOUR:SWE: Staircase')
plt.tight_layout()
plt.savefig(join(path_results, 'ex7_sean_staircase_sweep.png'), dpi=300)
plt.show()
plt.close()
