import pyvisa
import numpy as np
from os.path import join

GPIB = 23
num_points = 100
elements_sense = 'VOLTage, CURRent, RESistance, TIME'
# ---

rm = pyvisa.ResourceManager()
keithley = rm.open_resource("GPIB::{}".format(GPIB))
keithley.timeout = 10000  # set timeout to 5 seconds

# 0.
keithley.write('*RST')  # Restore GPIB default

keithley.write(':FORMat:ELEMents:SENSe ' + elements_sense)
keithley.write(':TRACe:TSTamp:FORMat ABSolute')

keithley.write(':SOUR:VOLT 10')  # Source 10V.
keithley.write(':TRAC:FEED SENS')  # Store raw readings in buffer.
keithley.write(':TRAC:POIN ' + str(num_points))  # Store 10 readings in buffer.
keithley.write(':TRAC:FEED:CONT NEXT')  # Enable buffer.
keithley.write(':TRIG:COUN ' + str(num_points))  # Trigger count = 10.
keithley.write(':OUTP ON')  # Turn on output.
keithley.write(':INIT')  # Trigger readings.
data = keithley.query_ascii_values(':TRACE:DATA?', container=np.array)  # Request raw buffer readings.
keithley.write(':CALC3:FORM MEAN')  # Select mean buffer statistic.
mean = keithley.query_ascii_values(':CALC3:DATA?', container=np.array)  # Request buffer mean data.
keithley.write(':CALC3:FORM SDEV')  # Select standard deviation statistic.
std = keithley.query_ascii_values(':CALC3:DATA?', container=np.array)  # Request standard deviation data.

""" Data Store Commands

:TRACe:DATA?                Read contents of buffer
:TRACe:CLEar                Clear buffer
:TRACe:FREE?                Read buffer memory status
:TRACe:POINts <n>           Specify buffer size (n = buffer size)
:TRACe:POINts:ACTual?       Query number of stored readings.
:TRACe:FEED <name>          Specify reading source. Name = SENSe[1] (raw readings)
:TRACe:FEED:CONTrol <name>  Start or stop buffer. Name = NEXT (fill buffer and stop) or NEVer (disable buffer)
:TRACe:TSTamp:FORMat <name> Select timestamp format. Name = ABSolute (reference to first buffer reading) or DELTa (time between buffer readings)
:CALCulate3:DATA?           Read buffer statistic data

"""

# --- The following is Sean code.

# Turn off output
keithley.write(':OUTP OFF')  # End example given in manual

print("Keithley (internal) mean: {}".format(mean))
print("Keithley (internal) std: {}".format(std))

# -

data_struct = np.reshape(data, (num_points, 4))

print("External mean: {}".format(np.mean(data_struct, axis=0)))
print("External std: {}".format(np.std(data_struct, axis=0)))

# -

import matplotlib.pyplot as plt
path_results = r'C:\Users\nanolab\PythonProjects\py-pennathur-lab\examples\darkroom\results'

sampling_rate = np.round(np.max(data_struct[:, 3]) / len(data_struct[:, 3]), 5)
print("Sampling Rate: {}".format(np.round(sampling_rate, 4)))
print("Time to sample 100 points: {}".format(np.round(sampling_rate * 100, 3)))
print("Time to sample 500 points: {}".format(np.round(sampling_rate * 500, 3)))

fig, ax = plt.subplots()
ax.plot(data_struct[:, 3], data_struct[:, 1], '-o',
        label=sampling_rate)
ax.set_xlabel('TSTamp (s)')
ax.set_ylabel('CURRent (A)')
ax.legend(title='Sampling rate (s)')

plt.suptitle('Constant VOLTage, :TRACe:DATA? from buffer')
plt.tight_layout()
plt.savefig(join(path_results, 'ex6_keithley_manual_data_store.png'), dpi=300)
plt.show()
plt.close()



