import pyvisa
import numpy as np



# Keithley 2410 - Trigger Channel 2
k_GPIB = 25
k_BoardIndex = 0

rm = pyvisa.ResourceManager()
print(rm.list_resources())  # only list "::INSTR" resources
print(rm.list_resources('?*'))  # list all resources
raise ValueError()
k1 = rm.open_resource('GPIB{}::{}::INSTR'.format(k_BoardIndex, k_GPIB))
k2 = None

# Initialize SMU1
k1.write('*RST')                    # Reset SMU #1
k1.write('TRIG:CLE')                # Clear any pending input triggers
# arm layer
k1.write('arm:dir acc')     # Wait for Arm event (IMM)  [ARM:DIRection (options: ACCeptor, SOURce)]
k1.write('arm:coun 1')      # Perform 1 scan (i.e., one lap around the ARM layer) (GPIB default = 1)
k1.write('arm:sour imm')    # Immediately go to Trig Layer [Arm Event Detector reads ARM:SOURce IMMediate]
k1.write('arm:outp none')   # No output triggers from scan (i.e., no outputs when passing from ARM to TRIGGER layers)
                            # [ARM:OUTPut (options: NONE, TENTer = Output Trigger)]
# trigger layer
k1.write('trig:dir acc')    # Wait for trigger event (TLINK)  [TRIGger:DIRection (options: ACCeptor, SOURce)]
k1.write('trig:coun 1')     # Perform 1 test (i.e., one lap around TRIGger layer) (GPIB default = 1)
k1.write('trig:sour imm')  # Trigger using Trigger Link  [TRIGger:SOURce (options: IMMediate, TLINk)]
k1.write('trig:outp sour')  # Output trigger after source "on"  [TRIGger:OUTPut (options: SOURce, DELay, SENSe)]
k1.write('trig:inp sens')   # Wait for trigger before measure [TRIGger:INPut (options: SOURce, DELay, SENSe)]
#k1.write('trig:ilin 1')     # Input trigger line
#k1.write('trig:olin 2')     # Output trigger line

# set up the measurements

source_voltage_range = 20  # Volts
source_voltage_level = 10  # Volts
sense_current_protection = 1e-3  # Amps
sense_current_range = 1e-3  # Amps

# 1. Select source function, mode
if k2 is None:
    keithley = k1
else:
    keithley = k2

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


# ---


# Turn on output
keithley.write(':OUTP ON')  # Output on before measuring.

# The following begins testing
keithley.write(':INIT')

# The following requests the measurement results and enters them into PC via GPIB bus.
data = keithley.query_ascii_values(':FETCh?', container=np.array)  # Initialize and ask for data

# Turn off output
keithley.write(':OUTP OFF')  # Output on before measuring.


print(data)

print('Program completed execution without errors.')