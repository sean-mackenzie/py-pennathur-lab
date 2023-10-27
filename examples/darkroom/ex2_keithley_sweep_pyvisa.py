


GPIB = 23
BoardIndex = 0

import pyvisa


# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
# 2. A KEITHLEY EXAMPLE

rm = pyvisa.ResourceManager()
keithley = rm.open_resource("GPIB::{}::INSTR".format(GPIB))
keithley.write("*rst")
keithley.write("status:preset")
keithley.write("*cls")
"""
Above, we create the instrument variable keithley, which is used for all further operations on the instrument. 
Immediately after it, we send the initialization and reset message to the instrument.
"""

interval_in_ms = 500
number_of_readings = 10
keithley.write("status:measurement:enable 512; *sre 1")
keithley.write("sample:count %d" % number_of_readings)
keithley.write("trigger:source IMM")
keithley.write("trigger:delay %f" % (interval_in_ms / 1000.0))
keithley.write("trace:points %d" % number_of_readings)
keithley.write("trace:feed sense1; trace:feed:control next")
"""
The above step is to write all the measurement parameters, in particular the interval time (500ms) and 
the number of readings (10) to the instrument. I won’t explain it in detail. Have a look at an SCPI and/or 
Keithley 2000 manual.
"""


"""
Okay, now the instrument is prepared to do the measurement. The above three lines make the instrument wait 
for a trigger pulse, trigger it, and wait until it sends a “service request”:
"""

keithley.write("initiate")
keithley.assert_trigger()
keithley.wait_for_srq()
"""
By sending the service request, the instrument tells us that the measurement has been finished and that 
the results are ready for transmission. 

We could read them with keithley.query(“trace:data?”) however, then we’d get:
-000.0004E+0,-000.0005E+0,-000.0004E+0,-000.0007E+0,
which we would have to convert to a Python list of numbers.
"""

voltages = keithley.query_ascii_values("trace:data?")
print("Average voltage: ", sum(voltages) / len(voltages))
""" read data from Keithley """

"""
Finally, we should reset the instrument’s data buffer and SRQ status register, 
so that it’s ready for a new run.
"""
keithley.query("status:measurement?")
keithley.write("trace:clear; trace:feed:control next")

keithley.close()