"""
The following is based on Keithley Application Note #2217:
Trigger Synchronization of Multiple series 2400 SourceMeter Instruments
"""

import pyvisa

# ---

# --- INSTRUMENT ADDRESSES

# Keithley 2410
k1_GPIB = 23
k1_BoardIndex = 1

# Keithley 2410
k2_GPIB = 23
k2_BoardIndex = 1

# Keithley 6517b
k3_GPIB = 23
k3_BoardIndex = 1

# Keithley Model 2361 Trigger Control Unit (TCU)
TCU_GPIB = 15
TCU_BoardIndex = 1

# ---

# --- COMMUNICATION

# Identify all available instruments
rm = pyvisa.ResourceManager()
print(rm.list_resources('?*'))  # returns something like: ('ASRL1::INSTR', 'ASRL2::INSTR', 'GPIB0::14::INSTR')

# --- initialize three Keithley Source-Measure Units (SMUs)
k1 = rm.open_resource('GPIB{}::{}::INSTR'.format(k1_BoardIndex, k1_GPIB))
k2 = rm.open_resource('GPIB{}::{}::INSTR'.format(k2_BoardIndex, k2_GPIB))
k3 = rm.open_resource('GPIB{}::{}::INSTR'.format(k3_BoardIndex, k3_GPIB))

# ---

"""

----------------- BEGIN EXAMPLE NOW

"""

"""
Example Application #2 (Three Instruments)

--- Background
SourceMeter #1 powers an LED.
SourceMeter #2 and #3 measure a photodetector affected by LED.

--- Procedure
1. SourceMeter #1 begins the first test on the LED.
2. SourceMeter #1 triggers SMU2 and SMU3 at the start of the test.
3. SMU #1 waits until SMU2 and SMU3 have completed their tests. 
4. SMU #1 then proceeds to the next test. 

*NOTE: the following code does not configure the SMUs to record data. It only sets up the Trigger Model.
To see how to setup the SMUs to record data, see Keithley_Two-Instrument-Trigger-Sync.py. 
"""

k1.write('*RST')  # Reset SMU #1
k1.write('TRIG:CLE')  # Clear any pending input triggers
k1.write('arm:coun 200')  # Perform # points in test
k1.write('arm:sour tlin')  # Wait for trigger from 2400 #3
k1.write('arm:dir sour')  # Skip 1st trigger event
k1.write('arm:outp none')  # No output triggers from scan
k1.write('arm:ilin 3')  # Define arm layer input line
k1.write('trig:coun 1')  # Perform one point of test
k1.write('trig:sour tlin')  # Trigger using Trigger Link
k1.write('trig:dir sour')  # Skip first trigger
k1.write('trig:outp sour')  # Output trigger after source "on"
k1.write('trig:inp sour')  # Wait for trigger before source
k1.write('trig:ilin 1')  # Input trigger line
k1.write('trig:olin 2')  # Output trigger line
k1.write('trig:del 0')  # Set trigger delay before source

k2.write('*RST')  # Reset SourceMeter #2
k2.write('TRIG:CLE')  # Clear any pending input triggers
k2.write('arm:coun 1')  # Perform only one scan
k2.write('arm:sour imm')  # Immediately start scan
k2.write('arm:dir acc')  # Wait for trigger event (IMM)
k2.write('arm:outp none')  # No output triggers from scan
k2.write('trig:coun 200')  # Perform # points in test
k2.write('trig:sour tlin')  # Trigger using Trigger Link
k2.write('trig:dir acc')  # Wait for first trigger
k2.write('trig:inp sour')  # Wait for trigger before source "on"
k2.write('trig:outp sens')  # Output trigger after measure
k2.write('trig:ilin 2')  # Input trigger line
k2.write('trig:olin 1')  # Output trigger line
k2.write('trig:del 0')  # Set trigger delay before source

k3.write('*RST')  # Reset SourceMeter #3
k3.write('TRIG:CLE')  # Clear any pending input triggers
k3.write('arm:coun 1')  # Perform only one scan
k3.write('arm:sour imm')  # Immediately start scan
k3.write('arm:dir acc')  # Wait for trigger event (IMM)
k3.write('arm:outp none')  # No output triggers from scan
k3.write('trig:coun 200')  # Perform # points in test
k3.write('trig:sour tlin')  # Trigger using Trigger Link
k3.write('trig:dir acc')  # Wait for first trigger
k3.write('trig:inp sour')  # Wait for trigger before source "on"
k3.write('trig:outp sens')  # Output trigger after measure
k3.write('trig:ilin 2')  # Input trigger line
k3.write('trig:olin 3')  # Output trigger line
k3.write('trig:del 0')  # Set trigger delay before source


print('Program completed execution without errors.')