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

rm = pyvisa.ResourceManager()

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

--- Procedure
1. SourceMeter #1 performs a current sweep from 1 to 10 mA in 1 mA steps (10 points).
2. At each sweep point:
    2.1 SMU1 will increase the source level,
    2.2 SMU1 will send an output trigger to SMU2,
    2.3 SMU1 will wait to "measure" the LED until it's triggered by SMU2. 
3. SMU2 waits to receive trigger from SMU1:
    3.1 SMU2 begins its measurement "sequence" immediately upon receiving the trigger from SMU1. 
    3.2 Immediately before SMU2 begins its "measurement", SMU2 sends a trigger to SMU1.
    This is to ensure both SMU2 and SMU1 "measurements" occur at exactly the same time.

*REMEMBER, each instrument goes through a "Source-Delay-Measure" sequence
where each step (Source, Delay, or Measure) can wait for a trigger before, or,
output a trigger after. 
"""

# --- CONFIGURING THE TRIGGER MODEL AND PROGRAMMING AND RUNNING A SWEEP

k1.write('*RST')                    # Reset SMU #1
k1.write('TRIG:CLE')                # Clear any pending input triggers
k1.write('syst:azer on')            # Ensure auto zero is enabled
k1.write('form:elem volt')          # Send only voltage readings to PC
k1.write('sour:cle:auto off')         # Automatically turn output ON/OFF
#k1.write('sour:cle:auto:mode: tco') # Output off after trigger count

# The following configures the Trigger Model for SMU1 (LED):
k1.write('arm:coun 1')      # Perform 1 sweep per ":INIT"
k1.write('arm:sour imm')    # Immediately go to Trig Layer
k1.write('arm:dir ACC')     # Wait for trigger event (IMM)
k1.write('arm:outp none')   # No output triggers from scan
k1.write('trig:coun 10')    # Perform # points in sweep
k1.write('trig:sour tlin')  # Trigger using Trigger Link
k1.write('trig:dir acc')    # Skip first trigger
k1.write('trig:outp sour')  # Output trigger after source "on"
k1.write('trig:inp sens')   # Wait for trigger before measure
# k1.write('trig:ilin 1')     # Input trigger line
# k1.write('trig:olin 2')     # Output trigger line
k1.write('trig:del 0')      # Set trigger delay before source

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

# The following configures SMU2 (photodetector) to perform a current measurement
# for every sweep step of SMU1 (LED). SMU1 will output a current,
# then trigger SMU2 to take its measurement. SMU2 then triggers SMU1 to
# signify it has completed its task.
k2.write('*RST')                    # Reset SourceMeter #2
k2.write('TRIG:CLE')                # Clear any pending input triggers
k2.write('syst:azer on')            # Ensure auto zero is enabled
k2.write('form:elem curr')          # Send only current readings to PC
k2.write('sour:cle:auto off')        # Automatically turn output ON/OFF
# k2.write('sour:cle:auto:mode tco')  # Turn off after trigger count

# The following configures the Trigger Model for SMU2:
k2.write('arm:coun 1')      # Perform only one scan
k2.write('arm:sour imm')    # Immediately start scan
k2.write('arm:dir acc')     # Wait for trigger event (IMM)
k2.write('arm:outp none')   # No output triggers from scan
k2.write('trig:coun 10')    # Perform # points in test
k2.write('trig:sour tlin')  # Trigger using Trigger Link
k2.write('trig:dir acc')    # Wait for first trigger
k2.write('trig:inp sour')   # Wait for trigger before source "on"
k2.write('trig:outp del')   # Output trigger after measure
# k2.write('trig:ilin 2')     # Input trigger line
# k2.write('trig:olin 1')     # Output trigger line
k2.write('trig:del 0')      # Set trigger delay before source

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