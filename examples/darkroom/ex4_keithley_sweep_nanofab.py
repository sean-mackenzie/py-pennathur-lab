
import pyvisa as visa             # PyVISA module for GPIB communication, installed
import time             # to allow pause between measurements
import os               # manipulate file paths and make directories
import numpy as np      # matlab-like array math



Keithley_GPIB_Addr = 23     # GPIB Address of the Keithley (in Menu/Comms)
CurrentCompliance = 1.00e-3    # compliance (max) current, in Amps

rm = visa.ResourceManager()
keithley = rm.open_resource(  'GPIB::' + str(Keithley_GPIB_Addr)  )

# Setup electrodes that are voltage
keithley.write("*RST")
time.sleep(0.5)    # add second between
keithley.write(":SOUR:FUNC:MODE VOLT")
keithley.write(":SENS:CURR:PROT:LEV " + str(CurrentCompliance))
keithley.write(":SENS:CURR:RANGE:AUTO 1")   # set current reading range to auto (boolean)
keithley.write(":OUTP ON")                    # Output on

V = 1
keithley.write(":SOUR:VOLT " + str(V))
data = keithley.write(":READ?")  # returns string with many values (V, I, ...)
print(data)

# keithley.write(":OUTP OFF")

keithley.write(":SOUR:FUNC:MODE curr")
keithley.write(":SOUR:CURR " + str(CurrentCompliance))
keithley.write(":SENS:volt:PROT:LEV " + str(max(V))  )
keithley.write(":SENS:volt:RANGE:AUTO 1")

keithley.write("SYSTEM:KEY 23") # go to local control
keithley.close()






