"""
The following is based on Keithley Application Note #2217:
Trigger Synchronization of Multiple series 2400 SourceMeter Instruments
"""

import pyvisa
import numpy as np

# ---

# --- INSTRUMENT ADDRESSES

# Keithley 2410 - Trigger Channel 1
k1_GPIB = 23
k1_BoardIndex = 1

# Keithley 2410 - Trigger Channel 2
k2_GPIB = 25
k2_BoardIndex = 0

# Keithley Model 2361 Trigger Control Unit (TCU)
TCU_GPIB = 15
TCU_BoardIndex = 1

# ---

# --- COMMUNICATION

# Identify all available instruments
rm = pyvisa.ResourceManager()
# print(rm.list_resources('?*'))  # returns something like: ('ASRL1::INSTR', 'ASRL2::INSTR', 'GPIB0::14::INSTR')

# --- initialize Keithley Model 2361 Trigger Control Unit (TCU)
"""TCU = rm.open_resource('GPIB{}::{}::INSTR'.format(TCU_BoardIndex, TCU_GPIB))
TCU.write('REN715')
TCU.write('DCL')"""

# initialize Keithley Model 2361 Trigger Control Unit (TCU)
""" NOTE: I may want to initialize/reset the TCU first, but I don't yet know how (10/25/23).

Below are some example trigger programs:
OUTPUT715;"1>2X"        If 1 is triggered, trigger out 2. 
OUTPUT715;"1*2>1X"      If 1 and 2 are triggered, trigger out 1.
"""
"""TCU.write('1>2;2>1*2X')  # P1: If SMU1 is triggered, trigger out 2; P2: If SMU2 is triggered, trigger out 1 and 2.
TCU.write('UNL')"""

# ---

# --- initialize three Keithley Source-Measure Units (SMUs)
k1 = rm.open_resource('GPIB{}::{}::INSTR'.format(k1_BoardIndex, k1_GPIB))
k2 = rm.open_resource('GPIB{}::{}::INSTR'.format(k2_BoardIndex, k2_GPIB))

"""

----------------- BEGIN EXAMPLE NOW

"""

"""
Example Application #1 (Two Instruments)

--- Background
SourceMeter #1 powers an LED.
SourceMeter #2 measures a photodetector affected by LED.
SMU1 and SMU2 communicate to perform a single-point test at the same time.

--- Process Flow (recall the Remote Trigger Model from 2410 User Manual, pg. 210 of PDF)
1. INIT command is sent to SMU1 and SMU2 --> moves SMU1 and SMU2 from IDLE into ARM layer.
2.1 SMU1 is configured to pass through ARM layer and immediately go to TRIGger layer.
2.2 SMU2 is configured to pass through ARM layer and immediately go to TRIGger layer.
3.1a SMU1 is configured to begin SOURcing.
3.1b Upon beginning SOURcing (of SDM cycle), SMU1 outputs a TRIGger to SMU2. 
3.1c SMU1 moves to DELay = 0 and so passes onto TRIGger, where SMU1 waits until a TRIGger is received before MEASuring. 
3.2 SMU2 is configured to wait until a TRIGger is received before SOURcing. 
4. Upon receiving a TRIGger via TLINk, SMU2 begins SOURCing.
5. SMU2 passes through DELay (of SDM cycle) and outputs a TRIGger via TLINk to SMU1. 
6. SMU1 receives TRIGger via TLINk from SMU2 and both SMU1 and SMU2 should perform MEASure action at same time.
7. Both SMU1 and SMU2 evaluate number of trigger layer cycles (TRIGger:COUNt = 1) so, NO. --> go to ARM layer. 
8. Both SMU1 and SMU2 evaluate number of arm layer cycles (ARM:COUNt = 1) so, NO. --> go to IDLE sate. 

--- How this should show up on the Model 2361 front panel LEDs:
1. SMU1 outputs a TRIGger to SMU2:
    --> LEDs that will blink: Ch.1 IN; Ch.2 OUT
2. SMU2 outputs a TRIGger to SMU1:
    --> LEDs that will blink: Ch.1 OUT; Ch.2 IN
"""

# --- CONFIGURING THE TRIGGER MODEL AND PROGRAMMING AND RUNNING A SWEEP

# ---

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
k1.write('trig:sour tlin')  # Trigger using Trigger Link  [TRIGger:SOURce (options: IMMediate, TLINk)]
k1.write('trig:outp sour')  # Output trigger after source "on"  [TRIGger:OUTPut (options: SOURce, DELay, SENSe)]
k1.write('trig:inp sens')   # Wait for trigger before measure [TRIGger:INPut (options: SOURce, DELay, SENSe)]
#k1.write('trig:ilin 1')     # Input trigger line
#k1.write('trig:olin 2')     # Output trigger line

# ---

# initialize SMU2
k2.write('*RST')            # Reset SourceMeter #2
k2.write('TRIG:CLE')        # Clear any pending input triggers
# arm layer
k2.write('arm:dir acc')     # Wait for Arm event (IMM)
k2.write('arm:coun 1')      # Perform 1 scan
k2.write('arm:sour imm')    # Immediately go to Trig Layer
k2.write('arm:outp none')   # No output triggers from scan
# trigger layer
k2.write('trig:dir acc')    # Wait for trigger event (TLINK)
k2.write('trig:coun 1')     # Perform 1 test
k2.write('trig:sour tlin')  # Trigger using Trigger Link
k2.write('trig:outp del')   # Output trigger after delay
k2.write('trig:inp sour')   # Wait for trigger before source
#k2.write('trig:ilin 1')     # Trigger link input line
#k2.write('trig:olin 2')     # Trigger Link output line

# ---

# set up the measurements

source_voltage_range = 20  # Volts
source_voltage_level = 10  # Volts
sense_current_protection = 1e-3  # Amps
sense_current_range = 1e-3  # Amps

# 1. Select source function, mode
for keithley in [k1, k2]:
    # keithley.write('*RST')  # Restore GPIB default

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
k1.write(':OUTP ON')  # Output on before measuring.
k2.write(':OUTP ON')  # Output on before measuring.

# The following begins testing
k2.write(':INIT')
k1.write(':INIT')

# The following requests the measurement results and enters them into PC via GPIB bus.
data2 = k2.query_ascii_values(':FETCh?', container=np.array)  # Initialize and ask for data
data1 = k1.query_ascii_values(':FETCh?', container=np.array)  # Initialize and ask for data

# Turn on output
k1.write(':OUTP OFF')  # Output on before measuring.
k2.write(':OUTP OFF')  # Output on before measuring.

print(data2)
print(data1)

print('Program completed execution without errors.')


# The below code is "CORRECT" --> It does what the example is supposed to do.
# The following code will produce TCU LEDs to light up: CH1. IN and OUT; CH2. IN and OUT
"""
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
k1.write('trig:sour tlin')  # Trigger using Trigger Link  [TRIGger:SOURce (options: IMMediate, TLINk)]
k1.write('trig:outp sour')  # Output trigger after source "on"  [TRIGger:OUTPut (options: SOURce, DELay, SENSe)]
k1.write('trig:inp sens')   # Wait for trigger before measure [TRIGger:INPut (options: SOURce, DELay, SENSe)]
#k1.write('trig:ilin 1')     # Input trigger line
#k1.write('trig:olin 2')     # Output trigger line

# ---

# initialize SMU2
k2.write('*RST')            # Reset SourceMeter #2
k2.write('TRIG:CLE')        # Clear any pending input triggers
# arm layer
k2.write('arm:dir acc')     # Wait for Arm event (IMM)
k2.write('arm:coun 1')      # Perform 1 scan
k2.write('arm:sour imm')    # Immediately go to Trig Layer
k2.write('arm:outp none')   # No output triggers from scan
# trigger layer
k2.write('trig:dir acc')    # Wait for trigger event (TLINK)
k2.write('trig:coun 1')     # Perform 1 test
k2.write('trig:sour tlin')  # Trigger using Trigger Link
k2.write('trig:outp del')   # Output trigger after delay
k2.write('trig:inp sour')   # Wait for trigger before source
#k2.write('trig:ilin 1')     # Trigger link input line
#k2.write('trig:olin 2')     # Trigger Link output line

# ---

# set up the measurements

source_voltage_range = 20  # Volts
source_voltage_level = 10  # Volts
sense_current_protection = 1e-3  # Amps
sense_current_range = 1e-3  # Amps

# 1. Select source function, mode
for keithley in [k1, k2]:
    # keithley.write('*RST')  # Restore GPIB default

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
k1.write(':OUTP ON')  # Output on before measuring.
k2.write(':OUTP ON')  # Output on before measuring.

# The following begins testing
k2.write(':INIT')
k1.write(':INIT')

# The following requests the measurement results and enters them into PC via GPIB bus.
data2 = k2.query_ascii_values(':FETCh?', container=np.array)  # Initialize and ask for data
data1 = k1.query_ascii_values(':FETCh?', container=np.array)  # Initialize and ask for data

# Turn on output
k1.write(':OUTP OFF')  # Output on before measuring.
k2.write(':OUTP OFF')  # Output on before measuring.

print(data2)
print(data1)
"""

# ---

# The below code is for reference --> it shows how to only trigger one instrument from the other.

# The following code will produce TCU LEDs to light up: CH1. IN; CH2. OUT
"""
The following code will produce TCU LEDs to light up: CH1. IN; CH2. OUT

NOTE: if you remove the 'trig:outp' line, then the TCU LEDs will not light up, nor will the 2nd device get triggered. 

# Initialize SMU1
k1.write('*RST')                    # Reset SMU #1
k1.write('TRIG:CLE')                # Clear any pending input triggers
k1.write('arm:dir acc')     # Wait for Arm event (IMM)  [ARM:DIRection (options: ACCeptor, SOURce)]
k1.write('arm:coun 1')      # Perform 1 scan (i.e., one lap around the ARM layer) (GPIB default = 1)
k1.write('arm:sour imm')    # Immediately go to Trig Layer [Arm Event Detector reads ARM:SOURce IMMediate]
k1.write('arm:outp none')   # No output triggers from scan (i.e., no outputs when passing from ARM to TRIGGER layers)
k1.write('trig:dir acc')    # Wait for trigger event (TLINK)  [TRIGger:DIRection (options: ACCeptor, SOURce)]
k1.write('trig:coun 1')     # Perform 1 test (i.e., one lap around TRIGger layer) (GPIB default = 1)
k1.write('trig:sour imm')  # Trigger using Trigger Link  [TRIGger:SOURce (options: IMMediate, TLINk)]
k1.write('trig:outp sour')  # Output trigger after source "on"  [TRIGger:OUTPut (options: SOURce, DELay, SENSe)]
k1.write('trig:olin 2')     # Output trigger line (LEDs that will blink: Ch.1 IN; Ch.2 OUT)

# initialize SMU2
k2.write('*RST')            # Reset SourceMeter #2
k2.write('TRIG:CLE')        # Clear any pending input triggers
k2.write('arm:dir acc')     # Wait for Arm event (IMM)
k2.write('arm:coun 1')      # Perform 1 scan
k2.write('arm:sour imm')    # Immediately go to Trig Layer
k2.write('arm:outp none')   # No output triggers from scan
k2.write('trig:dir acc')    # Wait for trigger event (TLINK)
k2.write('trig:coun 1')     # Perform 1 test
k2.write('trig:sour tlin')  # Trigger using Trigger Link
k2.write('trig:inp sens')   # Wait for trigger before source
"""

# The following code will produce the TCU LEDs to light up: CH1. OUT; CH2. IN
"""
The following code will produce the TCU LEDs to light up: CH1. OUT; CH2. IN

NOTE: if you remove the 'trig:outp' line, then the TCU LEDs will not light up, nor will the 2nd device get triggered. 

# Initialize SMU1
k1.write('*RST')                    # Reset SMU #1
k1.write('TRIG:CLE')                # Clear any pending input triggers
k1.write('arm:dir acc')     # Wait for Arm event (IMM)  [ARM:DIRection (options: ACCeptor, SOURce)]
k1.write('arm:coun 1')      # Perform 1 scan (i.e., one lap around the ARM layer) (GPIB default = 1)
k1.write('arm:sour imm')    # Immediately go to Trig Layer [Arm Event Detector reads ARM:SOURce IMMediate]
k1.write('arm:outp none')   # No output triggers from scan (i.e., no outputs when passing from ARM to TRIGGER layers)
k1.write('trig:dir acc')    # Wait for trigger event (TLINK)  [TRIGger:DIRection (options: ACCeptor, SOURce)]
k1.write('trig:coun 1')     # Perform 1 test (i.e., one lap around TRIGger layer) (GPIB default = 1)
k1.write('trig:sour tlin')  # Trigger using Trigger Link  [TRIGger:SOURce (options: IMMediate, TLINk)]
k1.write('trig:inp sens')   # Wait for trigger before measure [TRIGger:INPut (options: SOURce, DELay, SENSe)]

# initialize SMU2
k2.write('*RST')            # Reset SourceMeter #2
k2.write('TRIG:CLE')        # Clear any pending input triggers
k2.write('arm:dir acc')     # Wait for Arm event (IMM)
k2.write('arm:coun 1')      # Perform 1 scan
k2.write('arm:sour imm')    # Immediately go to Trig Layer
k2.write('arm:outp none')   # No output triggers from scan
k2.write('trig:dir acc')    # Wait for trigger event (TLINK)
k2.write('trig:coun 1')     # Perform 1 test
k2.write('trig:sour imm')  # Trigger using Trigger Link
k2.write('trig:outp sour')   # Output trigger after delay
k2.write('trig:olin 2')     # Trigger Link output line
"""

