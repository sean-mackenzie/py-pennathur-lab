"""
NOTE: this program is confirmed to work with Keithley (9/18/2023)
"""

import pyvisa
import numpy as np

GPIB = 23

source_voltage_range = 20  # Volts
source_voltage_level = 10  # Volts
sense_current_protection = 1e-3  # Amps
sense_current_range = 1e-3  # Amps

# ---

rm = pyvisa.ResourceManager()
keithley = rm.open_resource("GPIB::{}".format(GPIB))

# 0.
keithley.write('*RST')  # Restore GPIB default

# 1. Select source function, mode
keithley.write(':SOUR:FUNC VOLT')  # Select voltage source.
keithley.write(':SOUR:VOLT:MODE FIXED')  # Fixed voltage source mode.

# 2. Set source range, level, compliance
keithley.write('SOUR:VOLT:RANG ' + str(source_voltage_range))  # Select 20V source range.
keithley.write(':SOUR:VOLT:LEV ' + str(source_voltage_level))  # Source output = 10V.
keithley.write(':SENS:CURR:PROT ' + str(sense_current_protection))  # 1mA compliance.

# 3. Set measure function, range
keithley.write(':SENS:FUNC "CURR"')  # Current measure function.
keithley.write(':SENS:CURR:RANG ' + str(sense_current_range))  # 1mA measure range.
keithley.write(':FORM:ELEM CURR')  # Current reading only.

# 4. Turn on output
keithley.write('OUTP ON')  # Output on before measuring.

# 5. Read data
data = keithley.query_ascii_values(':READ?', container=np.array)  # Trigger, acquire reading.
# NOTE: Instrument must be addressed to talk after :READ? to acquire data.

# 6. Turn off output
keithley.write(':OUTP OFF')  # End example given in manual

# I assume you would want to shut down the device after this...
# NOTE: 9/18/2023 - It actually seems like this shuts down the instrument just fine because I can ru-run program.

print(data)
