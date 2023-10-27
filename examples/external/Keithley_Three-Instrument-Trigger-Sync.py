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

# Keithley 6517b
k3_GPIB = 27
k3_BoardIndex = 3

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
To see how to setup the SMUs to record data, see Keithley_Two-Instrument-Trigger-Sync-Sweep.py. 
"""

k1.write('*RST')  # Reset SMU #1
k1.write('TRIG:CLE')  # Clear any pending input triggers
k1.write('arm:coun 40')  # Perform # points in test
k1.write('arm:sour tlin')  # Wait for trigger from 2400 #3
k1.write('arm:dir sour')  # Skip 1st trigger event
k1.write('arm:outp none')  # No output triggers from scan
# k1.write('arm:ilin 3')  # Define arm layer input line
k1.write('trig:coun 1')  # Perform one point of test
k1.write('trig:sour tlin')  # Trigger using Trigger Link
k1.write('trig:dir sour')  # Skip first trigger
k1.write('trig:outp sour')  # Output trigger after source "on"
k1.write('trig:inp sour')  # Wait for trigger before source
# k1.write('trig:ilin 1')  # Input trigger line
# k1.write('trig:olin 2')  # Output trigger line
k1.write('trig:del 0')  # Set trigger delay before source

k2.write('*RST')  # Reset SourceMeter #2
k2.write('TRIG:CLE')  # Clear any pending input triggers
k2.write('arm:coun 1')  # Perform only one scan
k2.write('arm:sour imm')  # Immediately start scan
k2.write('arm:dir acc')  # Wait for trigger event (IMM)
k2.write('arm:outp none')  # No output triggers from scan
k2.write('trig:coun 40')  # Perform # points in test
k2.write('trig:sour tlin')  # Trigger using Trigger Link
k2.write('trig:dir acc')  # Wait for first trigger
k2.write('trig:inp sour')  # Wait for trigger before source "on"
k2.write('trig:outp sens')  # Output trigger after measure
# k2.write('trig:ilin 2')  # Input trigger line
# k2.write('trig:olin 1')  # Output trigger line
k2.write('trig:del 0')  # Set trigger delay before source

# Keithley 6517b code needs some work but it does output the requested buffer (but non ASCII format)
k3.write('*RST')  # Reset SourceMeter #3
# k3.write('trig:sour ext;coun inf')
k3.write('trig:coun 20')
k3.write('trac:poin 20; elem curr')
k3.write('trac:feed:cont next')
"""
k3.write('arm:coun 1')  # Perform only one scan
k3.write('arm:sour imm')  # Immediately start scan
k3.write('arm:tcon:dir acc')  # Wait for trigger event (IMM)
k3.write('arm:outp none')  # No output triggers from scan
k3.write('trig:coun 200')  # Perform # points in test
k3.write('trig:sour tlin')  # Trigger using Trigger Link
k3.write('trig:dir acc')  # Wait for first trigger
k3.write('trig:inp sour')  # Wait for trigger before source "on"
k3.write('trig:outp sens')  # Output trigger after measure
# k3.write('trig:ilin 2')  # Input trigger line
# k3.write('trig:olin 3')  # Output trigger line
k3.write('trig:del 0')  # Set trigger delay before source
"""

# --- Sean additions

k1.write('syst:azer on')            # Ensure auto zero is enabled
k1.write('form:elem volt')          # Send only voltage readings to PC
k1.write('sour:cle:auto off')         # Automatically turn output ON/OFF
# The following configures the measurement and voltage bias for SMU1 (LED):
k1.write('sour:func curr')          # Output constant current
k1.write('sens:func "volt"')        # Measure forward voltage of LED
k1.write('sour:curr:star 0.001')    # Start point for sweep
k1.write('sour:curr:stop 0.01')     # Stop point for sweep
k1.write('sour:curr:step 0.001')    # Define sweep step size
k1.write('sour:curr:rang 0.01')     # Set fixed measurement range
k1.write('sour:del 0.001')          # Set source delay before measure
k1.write('sens:volt:prot 2')        # 2V compliance range
k1.write('sens:volt:rang 2')        # Measure on 2V range
k1.write('sens:volt:nplc 1')        # Measurement integration
k1.write('sour:curr:mode swe')      # Perform sweep function

k2.write('syst:azer on')            # Ensure auto zero is enabled
k2.write('form:elem curr')          # Send only current readings to PC
k2.write('sour:cle:auto off')        # Automatically turn output ON/OFF
# The following configures the measurement and voltage bias for SMU2:
k2.write('sour:func volt')          # Output constant voltage
k2.write('sens:func "curr"')        # Measure leakage current of photodetector
k2.write('sour:curr:rang:auto on')  # Enable source auto range
k2.write('sour:volt 5')             # Set output level
k2.write('sour:del 0.01')           # Set source delay before measure
k2.write('sens:curr:prot 0.01')     # 10mA compliance range
k2.write('sens:curr:rang 0.01')     # Measure on 10mA range
k2.write('sens:curr:nplc 1')        # Measurement integration
# ---

# Turn on output
k1.write(':OUTP ON')  # Output on before measuring.
k2.write(':OUTP ON')  # Output on before measuring.
k3.write(':OUTP ON')  # Output on before measuring.

# The following begins testing
k3.write(':INIT')
k2.write(':INIT')
k1.write(':INIT')

# The following requests the measurement results and enters them into PC via GPIB bus.
data2 = k2.query_ascii_values(':FETCh?', container=np.array)  # Initialize and ask for data
data1 = k1.query_ascii_values(':FETCh?', container=np.array)  # Initialize and ask for data

data3 = k3.query('trac:data?')

# Turn on output
k1.write(':OUTP OFF')  # Output on before measuring.
k2.write(':OUTP OFF')  # Output on before measuring.
k3.write(':OUTP OFF')  # Output on before measuring.

print(data3)
print(data2)
print(data1)

print('Program completed execution without errors.')