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

---

NOTES ON TRIGGER OPERATION:

1. If a trigger is received on a channel that is not used in an input expression, the "IN" LED will turn on and remain
lit until that channel is cleared.

1. The "IN" LED will blink when a trigger is received on that channel.
2. The "OUT" LED will blink when a trigger is sent to that channel. (not sure what that means, I quoted the manual).


---

NOTES ON TRIGGER PROGRAMMING:

The following is a list of example programs from the Model 2361 Trigger Control Unit manual:
    OUTPUT715;"1>2X"        If 1 is triggered, trigger out 2.
    OUTPUT715;"1*2>1X"     If 1 and 2 are triggered, trigger out 1.

Operators:
    "1" and "2" are the channels.
    "*" is the LOGICAL AND operator.
    ">" is the I/O separator. It separates the input expression from the output expression.
    "X" commands the TCU to execute the current program.

"""

import pyvisa
import time

GPIB = 15
BoardIndex = 2

# ---

# open resource manager
rm = pyvisa.ResourceManager()

# open instrument: Keithley Model 2361 Trigger Control Unit (TCU)
TCU = rm.open_resource('GPIB{}::{}::INSTR'.format(BoardIndex, GPIB))

# clear the present program
TCU.write('C0X')

# unlatch triggers for all channels
for i in range(6):
    TCU.write('I{}X'.format(i + 1))  # TCU command (In): "I" is the command to unlatch trigger; "n" is the channel.
    time.sleep(0.5)  # add delay to watch triggers sequentially unlatch

# send a trigger pulse to each channel
for i in range(6):
    TCU.write('P{}X'.format(i + 1)) # TCU command: (Pn): "P" is command to send immediate pulse.
    time.sleep(0.5)  # add delay to watch triggers sequentially pulse

# program trigger events
TCU.write('2>3;1>2X')   # ";" links multiple relations. ">" corresponds to: if trigger in A, then trig out B
time.sleep(2)           # add delay to watch if ERROR LED turns ON.

# clear the instrument (general VISA command to clear instrument. NOTE, this clears the programmed trigger as well)
TCU.clear()

# close the instrument
TCU.close()

print("Program completed without errors.")
