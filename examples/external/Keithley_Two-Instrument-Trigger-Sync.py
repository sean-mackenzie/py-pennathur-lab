"""
The following is based on Keithley Application Note #2217:
Trigger Synchronization of Multiple series 2400 SourceMeter Instruments
"""

import pyvisa
import numpy as np

# ---

# --- INSTRUMENT ADDRESSES

# Keithley 2410
k1_GPIB = 23
k1_BoardIndex = 1

# Keithley 2410
k2_GPIB = 25
k2_BoardIndex = 0

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


# ---

"""

----------------- BEGIN EXAMPLE NOW

"""

"""
Example Application #1 (Two Instruments)

--- Background
SourceMeter #1 powers an LED.
SourceMeter #2 measures a photodetector affected by LED.
SMU1 and SMU2 communicate to perform a single-point test at the same time.
"""

# --- CONFIGURING THE TRIGGER MODEL AND PROGRAMMING AND RUNNING A SWEEP

# Initialize SMU1
k1.write('*RST')                    # Reset SMU #1
k1.write('TRIG:CLE')                # Clear any pending input triggers

# The following configures the Trigger Model for SMU1 (LED):

# arm layer
k1.write('arm:dir acc')     # Wait for Arm event (IMM)
k1.write('arm:coun 1')      # Perform 1 scan
k1.write('arm:sour imm')    # Immediately go to Trig Layer
k1.write('arm:outp none')   # No output triggers from scan

# trigger layer
k1.write('trig:dir acc')    # Wait for trigger event (TLINK)
k1.write('trig:coun 1')     # Perform 1 test
k1.write('trig:sour tlin')  # Trigger using Trigger Link
k1.write('trig:outp sour')  # Output trigger after source "on"
k1.write('trig:inp sens')   # Wait for trigger before measure
k1.write('trig:ilin 1')     # Input trigger line
k1.write('trig:olin 2')     # Output trigger line


# initialize SMU2
k2.write('*RST')            # Reset SourceMeter #2
k2.write('TRIG:CLE')        # Clear any pending input triggers

# The following configures the Trigger Model for SMU2 (Photodetector):

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
k2.write('trig:ilin 2')     # Trigger link input line
k2.write('trig:olin 1')     # Trigger Link output line

# The following begins testing and enters results into PC via GPIB bus.
data2 = k2.query_ascii_values(':READ?', container=np.array)  # Initialize and ask for data
data1 = k1.query_ascii_values(':READ?', container=np.array)  # Initialize and ask for data


print('Program completed execution without errors.')