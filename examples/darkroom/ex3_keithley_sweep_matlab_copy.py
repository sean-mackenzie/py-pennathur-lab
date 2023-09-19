

GPIB = 23

import pyvisa
import time


# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
# 2. A KEITHLEY EXAMPLE

vout = 1
CurrentCompliance = 1.00e-3    # compliance (max) current, in Amps
I_range = 200e-6

rm = pyvisa.ResourceManager()
keithley = rm.open_resource("GPIB::{}::INSTR".format(GPIB))
# keithley.write("*rst; status:preset; *cls")

keithley.write("*RST")
time.sleep(0.5)

# keithley.write(":SOUR:FUNC:MODE VOLT")
# keithley.write(":SENS:CURR:PROT:LEV " + str(CurrentCompliance))
# keithley.write(":SENS:CURR:RANGE:AUTO 1")   # set current reading range to auto (boolean)

keithley.write(":SOUR:FUNC:MODE VOLT")
keithley.write(":SOUR:VOLT:MODE FIX")
keithley.write(":SOUR:VOLT:RANG " + str(vout))
keithley.write(':SENS:FUNC "CURR"')
keithley.write(":SENS:CURR:PROT:LEV " + str(CurrentCompliance))
keithley.write(":SENS:CURR:RANG " + str(I_range))
# keithley.write(":SENS:CURR:RANGE:AUTO 1")   # set current reading range to auto (boolean)
keithley.write(":DISP:ENAB ON")
keithley.write(":SOUR:DEL 0")
keithley.write(":ROUT:TERM FRON")
keithley.write(":FORM:SREG ASC")
keithley.write("FORM:ELEM VOLT, CURR")

print("Keithley opened!")

keithley.write(":OUTP ON")

keithley.write(":SOUR:VOLT:LEV 0")
keithley.write(":INIT")
data = keithley.write(":FETC?")
print(data)

keithley.write(":SOUR:VOLT:LEV 1")
keithley.write(":INIT")
data = keithley.write(":FETC?")
print(data)

# ---

keithley.write(":SOUR:VOLT 0")
time.sleep(0.5)
keithley.write(":OUTP OFF")
time.sleep(0.5)
keithley.write("*RST")

time.sleep(0.5)

rm.close()






