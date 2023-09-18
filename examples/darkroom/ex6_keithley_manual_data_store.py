import pyvisa
import numpy as np

GPIB = 23

# ---

rm = pyvisa.ResourceManager()
keithley = rm.open_resource("GPIB::{}".format(GPIB))

# 0.
keithley.write('*RST')  # Restore GPIB default
keithley.write(':SOUR:VOLT 10')  # Source 10V.
keithley.write(':TRAC:FEED SENS')  # Store raw readings in buffer.
keithley.write(':TRAC:POIN 10')  # Store 10 readings in buffer.
keithley.write(':TRAC:FEED:CONT NEXT')  # Enable buffer.
keithley.write(':TRIG:COUN 10')  # Trigger count = 10.
keithley.write(':OUTP ON')  # Turn on output.
keithley.write(':INIT')  # Trigger readings.
keithley.query_ascii_values(':TRACE:DATA?', container=np.array)  # Request raw buffer readings.
keithley.write(':CALC3:FORM MEAN')  # Select mean buffer statistic.
keithley.query_ascii_values(':CALC3:DATA?', container=np.array)  # Request buffer mean data.
keithley.write(':CALC3:FORM SDEV')  # Select standard deviation statistic.
keithley.query_ascii_values(':CALC3:DATA?', container=np.array)  # Request standard deviation data.

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