


GPIB = 23
BoardIndex = 0

import pyvisa

# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
# 1. A GENERAL EXAMPLE

rm = pyvisa.ResourceManager()
print(rm)
"""
After importing pyvisa, we create a ResourceManager object. If called without arguments,
PyVISA will prefer the default backend (IVI) which tries to find the VISA shared library 
for you. If it fails it will fall back to pyvisa-py if installed. You can check what backend 
is used and the location of the shared library used, if relevant, simply by:

print(rm)
# returns somethign like: <ResourceManager('/path/to/visa.so')>

"""

print(rm.list_resources())
# returns something like: ('ASRL1::INSTR', 'ASRL2::INSTR', 'GPIB0::14::INSTR')

my_instrument = rm.open_resource('GPIB0::{}::INSTR'.format(GPIB))
"""
Once that you have a ResourceManager, you can list the available resources using the list_resources method. 
The output is a tuple listing the VISA resource names. You can use a dedicated regular expression syntax to 
filter the instruments discovered by this method. The syntax is described in details in list_resources(). 
The default value is ‘?*::INSTR’ which means that by default only instrument whose resource name ends 
with ‘::INSTR’ are listed (in particular USB RAW resources and TCPIP SOCKET resources are not listed). 
To list all resources present, pass ‘?*’ to list_resources.

In this case, there is a GPIB instrument with instrument number 14, so you ask the ResourceManager to 
open “‘GPIB0::14::INSTR’” and assign the returned object to the my_instrument.

Notice open_resource has given you an instance of GPIBInstrument class (a subclass of the more generic Resource).
"""

print(my_instrument.query('*IDN?'))
"""
Then, you query the device with the following message: '\*IDN?'. Which is the standard GPIB message for 
“what are you?” or – in some cases – “what’s on your display at the moment?”. query is a short form for 
a write operation to send a message, followed by a read.
"""


# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
# 2. A KEITHLEY EXAMPLE

rm = pyvisa.ResourceManager()
keithley = rm.open_resource("GPIB::{}".format(GPIB))
keithley.write("*rst; status:preset; *cls")
"""
Above, we create the instrument variable keithley, which is used for all further operations on the instrument. 
Immediately after it, we send the initialization and reset message to the instrument.
"""

interval_in_ms = 500
number_of_readings = 10
keithley.write("status:measurement:enable 512; *sre 1")
keithley.write("sample:count %d" % number_of_readings)
keithley.write("trigger:source bus")
keithley.write("trigger:delay %f" % (interval_in_ms / 1000.0))
keithley.write("trace:points %d" % number_of_readings)
keithley.write("trace:feed sense1; trace:feed:control next")
"""
The above step is to write all the measurement parameters, in particular the interval time (500ms) and 
the number of readings (10) to the instrument. I won’t explain it in detail. Have a look at an SCPI and/or 
Keithley 2000 manual.
"""

keithley.write("initiate")
keithley.assert_trigger()
keithley.wait_for_srq()
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
"""

voltages = keithley.query_ascii_values("trace:data?")
print("Average voltage: ", sum(voltages) / len(voltages))
""" read data from Keithley """

keithley.query("status:measurement?")
keithley.write("trace:clear; trace:feed:control next")
"""
Finally, we should reset the instrument’s data buffer and SRQ status register, so that it’s ready for a new run.
"""
