"""

First, some important notes:

FRONT PANEL INDICATORS:

"TALK"
    * The "TALK" LED is ON when the instrument is in the talker active state.
    * The unit is placed in this state by addressing it to talk.
    * The "TALK" LED is OFF when the unit is in the talker idle state.

"LISTEN"
    * The "LISTEN" LED is ON when the unit is in the listener active state.
    * The "LISTEN" LED is OFF when the unit is in the listener idle state.

"REMOTE"
    * The LED is ON when in the remote state. (not sure what the "remote state" is)
    * The LED is OFF when in the local state. (not sure what the "local state" is)

"ERROR"
The error LED will turn on when one of the following conditions occurs:
    * Trigger test failed
    * Digital I/O test failed
    * ROM test failed
    * RAM test failed
    * Illegal device-dependent command option (IDDCO)
    * Illegal device-dependent command (IDDC)

NOTES ON POWERING ON THE TCU:

0. There is a "self-test" procedure however this requires hooking up all trigger and
    digital inputs and outputs to each other (which I don't want to do).
1. When I power on the TCU and no instruments are powered on,
    --> only the POWER ON LED is ON.
2. If I power on an instrument (e.g., Keithley),
    --> The "IN" LED corresponding to the Keithle's "CHANNEL #" turns ON.
3. If I power off that same instrument,
    --> The "IN" LED remains turned ON.
---> Maybe this means that the Keithley's internal program automatically outputs a trigger upon initialization,
---> and, that I need to first clear any triggers from the Keithley?

# ---

NOTES ON COMMUNICATING WITH THE TCU:

When I run the following code:
---
TCU = rm.open_resource('GPIB{}::{}::INSTR'.format(BoardIndex, GPIB))
TCU.write('*IDN?')
print(TCU.read_bytes(25))
---
I get the message:      b'255\r\n255\r\n255\r\n255\r\n255\r\n'

But, when I run:
---
print(TCU.query('*IDN?'))
---
I get the message: 255

--> This means to me that the default read/write terminations must be correct.
--> However, the TCU LED's for "TALK" and "ERROR" remain ON after querying.
--> --> Does that mean there is an error?

Additionally, when I inspect the device in debugger mode:
    * after running: TCU = rm.open_resource('GPIB{}::{}::INSTR'.format(BoardIndex, GPIB))
I get the following properties by default:
    * CR = '\r'
    * LF = '\n'
    * encoding = 'ascii'
    * read_termination = None
    * write_termination = '\r\n'
    * timeout = 3000


---

NOTES ON TRIGGER OPERATION:

1. If a trigger is received on a channel that is not used in an input expression, the "IN" LED will turn on and remain
lit until that channel is cleared.

1. The "IN" LED will blink when a trigger is received on that channel.
2. The "OUT" LED will blink when a trigger is sent to that channel. (not sure what that means, I quoted the manual).


---

NOTES ON TRIGGER PROGRAMMING:

The following is a list of example programs from the Model 2361 Trigger Control Unit manual:

Simple examples:

OUTPUT715;"1>2X"        If 1 is triggered, trigger out 2.

OUTPUT715;"1*2>1X"     If 1 and 2 are triggered, trigger out 1.

Example of simple examples:

I think "OUTPUT715;" is akin to "keithley.write(" ") statement. Not sure yet though (10/25/23).

"1" and "2" are the channels.

"*" is the LOGICAL AND operator.

">" is the I/O separator. It separates the input expression from the output expression.

"X" commands the TCU to execute the current program.

"""

import pyvisa

GPIB = 15
BoardIndex = 2

rm = pyvisa.ResourceManager()
print(rm.list_resources('?*'))  # returns something like: ('ASRL1::INSTR', 'ASRL2::INSTR', 'GPIB0::14::INSTR')

# TCU = rm.open_resource('GPIB{}::{}::INSTR'.format(BoardIndex, GPIB))
# print(TCU.query('*IDN?'))

"""
Then, you query the device with the following message: '\*IDN?'. Which is the standard GPIB message for 
“what are you?” or – in some cases – “what’s on your display at the moment?”. query is a short form for 
a write operation to send a message, followed by a read.

The response of each instrument is as follows:

Keithley Model 2361 Trigger Control Unit:       255         (the "TALK" and "ERROR" LED's turn red)

"""


# ---
""" TESTING THINGS """


TCU = rm.open_resource('GPIB{}::{}::INSTR'.format(BoardIndex, GPIB)) # , read_termination='\r\n')
print(TCU.query('*IDN?'))

"""TCU.write('*IDN?')
print(TCU.read_bytes(25))
"""

"""
Additionally, when I inspect the device in debugger mode:
    * after running: TCU = rm.open_resource('GPIB{}::{}::INSTR'.format(BoardIndex, GPIB))
I get the following properties by default:
    * CR = '\r'
    * LF = '\n'
    * encoding = 'ascii'
    * read_termination = None
    * write_termination = '\r\n'
    * timeout = 3000
"""