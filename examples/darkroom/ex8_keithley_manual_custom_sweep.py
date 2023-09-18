import pyvisa
import numpy as np

GPIB = 23

# ---

rm = pyvisa.ResourceManager()
keithley = rm.open_resource("GPIB::{}".format(GPIB))

# 0.
keithley.write('*RST')  # Restore GPIB default
keithley.write(':SENS:FUNC:CONC OFF')  # Turn off concurrent functions.
keithley.write(':SOUR:FUNC VOLT')  # Volts source function.
keithley.write(':SENS:FUNC ‘CURR:DC’')  # Current sense function.
keithley.write(':SENS:CURR:PROT 0.1')  # 100mA current compliance.
keithley.write(':SOUR:VOLT:MODE LIST')  # List volts sweep mode.
keithley.write(':SOUR:LIST:VOLT 7,1,3,8,2')  # 7V, 1V, 3V, 8V, 2V sweep points.
keithley.write(':TRIG:COUN 5')  # Trigger count = # sweep points.
# NOTE:
#       * For single sweep, trigger count should equal number of points in the sweep: Points = (Stop-Start)/Step + 1.
#       * You can use ':SOUR:SWE:POIN?' query to read the number of points.
keithley.write(':SOUR:DEL 0.1')  # 100ms source delay.
keithley.write(':OUTP ON')  # Turn on source output.
keithley.query_ascii_values(':READ?', container=np.array)  # Trigger sweep, request data.

""" Custom sweep commands

:SOURce:VOLTage:MODE LIST               Select voltage list (custom) sweep mode.
:SOURce:LIST:VOLTage < list>            Define V-source list (list = V1, V2,... Vn).
:SOURce:LIST:VOLTage:APPend <list>      Add V-source list value(s) (list =V1, V2,...Vn).
:SOURce:LIST:VOLTage:POINts?            Query length of V-source list.
:SOURce:SWEep:RANGing <name>            Select source ranging (name = BEST, AUTO, or FIXed).
"""