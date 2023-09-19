import pyvisa
import numpy as np

GPIB = 23

# ---

rm = pyvisa.ResourceManager()
keithley = rm.open_resource("GPIB::{}".format(GPIB))

# 0.
keithley.write('*RST')  # Restore GPIB default
keithley.write(':SENS:FUNC:CONC OFF')  # Turn off concurrent functions.
keithley.write(':SOUR:FUNC CURR')  # Current source function.
keithley.write(':SENS:FUNC "VOLT:DC"')  # Volts sense function.
keithley.write(':SENS:VOLT:PROT 1')  # 1V voltage compliance.
keithley.write(':SOUR:CURR:START 1E-3')  # 1mA start current.
keithley.write(':SOUR:CURR:STOP 10E-3')  # 10mA stop current.
keithley.write(':SOUR:CURR:STEP 1E-3')  # 1mA step current.
keithley.write(':SOUR:CURR:MODE SWE')  # Select current sweep mode.
keithley.write(':SOUR:SWE:RANG AUTO')  # Auto source ranging.
keithley.write(':SOUR:SWE:SPAC LIN')  # Select linear staircase sweep.
keithley.write(':TRIG:COUN 10')  # Trigger count = # sweep points.
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

print(data)