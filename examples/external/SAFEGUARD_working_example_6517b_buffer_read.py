from pymeasure.instruments.keithley import Keithley6517B
import time

"""
REFERENCE: https://forums.ni.com/t5/Instrument-Control-GPIB-Serial/Help-reading-buffer-in-Keithley-Electrometer-6517B-through-SCPI/td-p/4356861

The code below (i.e., RAW CODE) was given in a forum as code that did not enable reading data from the buffer. 
Later on in the forum discussion, the author followed up with two additional statements that enabled correctly 
reading from the buffer. These two lines were:
    ':SYST:LSYNC:STAT 0'            (which should follow the ':SYST:ZCH OFF' command)
    ':TRACE:ELEM NONE'              (it's not understood at present if this command is necessary to enable buffer)

(RAW CODE)          (NOTE: this is not necessarily the code that worked for me but it was my template)
*RST
:SYST:ZCH ON
:FORMAT:ELEM READ
:FORMAT:DATA SRE
:SENSE:FUNC 'VOLT'
:SENSE:VOLT:RANGE 20
:SENSE:VOLT:NPLC 0.01
:SENS:VOLT:AVERAGE:TYPE NONE
:SENS:VOLT:MED:STAT OFF

:DISP:ENABLE OFF
:SYST:ZCH OFF

:TRACE:FEED:CONT NEVER
:TRACE:CLEAR
:TRACE:POINTS 100
:TRIG:COUNT 100
:TRIG:DELAY 0
:TRACE:FEED:CONT NEXT
:INIT

:TRACE:DATA?

---

The functional code below is the first working copy that (for me) enabled reading from the buffer. 
The code is copied verbatim here for safekeeping. It can be extended to future scripts but should not be modified.
"""

"""
Discussion on why these these commands *seem* to be the solution to reading from the buffer

1. ':SYST:LSYNC:STAT 0'
        * This command sets the Line Synchronization (pg. 43 of 6517b programming manual). 
            * When line synchronization is enabled, measurements are initiated at the first positive=going zero crossing
            of the power line cycle after the trigger. In other words, A/D conversion (like NPLC) is synchronized
            to the power line cycle--which increases common mode and normal mode rejection. 
            * By default, line synchronization is enabled. 
            * This line of code disables line synchronization.
                ** Perhaps, when line synchronization is enabled:
                    *** buffer readings are disabled because they cannot occur at the rate specified by NPLC. 
                    *** Or, because line synchronization requires triggering each measurement (see page 43 for a nice
                    graphic of this) and therefore only one measurement can be made per trigger (i.e., per :INIT).
                ** Perhaps, in contrast, when line synchronization is disabled:
                    *** the buffer is able to fill with data after only one trigger (i.e., :INIT). 
                    *** This reasoning makes the most sense to me, as of right now. 
        * Changing the state of line synchronization halts triggers and puts the instrument into idle. Pressing the 
            TRIG key will return to re-arm triggers. 
                    *** Perhaps halting triggers and putting the instrument in idle is necessary for buffer readings? 
        *** If disabling line synchronization enables buffer reading b/c triggering:
            * This points to potential other means of enabling buffer reading. 
                * For example, by instructing the trigger model to perform multiple loops around the ARM or TRIG layers.

2. ':TRACE:ELEM NONE'
        * This command instructs the instrument to store extra data with each reading, such as voltage level. 
        * It is interesting to note that the example programming script for how to store readings in teh buffer
        (see pg. 36 of Keithley6517b programming manual) also uses this command (i.e., TRAC:ELEM NONE). 
        * It is interesting to note that the example programming script for reading buffer data from multiple channels
        (see pg. 38 of 6517b programming manual) also uses this command (i.e., TRAC:ELEM NONE) but then, at the 
        very end of the script, after the buffer reading has completed (but before the data in the buffer has been
        read out via :TRAC:DATA?), they assert :FORM:ELEM READ,TIME,CHAN and then :TRAC:DATA?. 
            ** This seems like it would yield the desired data elements (i.e., reading, timestamp, and channel) 
            and is made even more interesting by the fact that they initially asserted :TRAC:ELEM NONE. 
                *** This is something that I will have to test out. 
                *** Perhaps, telling the instrument to include other data in the buffer somehow confuses it. 
        * Note: the default parameters for:
            :FORM:ELEM --> READ,CHAN,RNUM,UNIT,TST,STAT     (optional: VSOurce)
            :TRAC:ELEM --> NONE? (no default is given)      (optional: TST,CHAN,VSOurce,NONE)
                (pg. 351): "READing, STATus, RNUMber (reading number), and UNIT are always enabled for the buffer 
                and are included in the response for the query."
            
        * A note on :TRAC:DATA?
            ** "When this command is sent and the 6517B is addressed to talk, all the readings stored in the buffer
            are sent to the computer. The format in which the readings are sent over the bus is controlled by the
            FORMat subsystem."
            ** "The buffer elements selected by :TRACe:ELEMents must match the bus elements selected
            by :FORMat:ELEMents. Otherwise, the following error occurs when using this command to send
            buffer readings over the bus: +313 Buffer & format element mismatch."

3. ':FORMAT:DATA SRE'
        * This command configures the data format that is used when transferring readings over the remote interface.
        (see page 242 of Keithley 6517b programming manual). 
            ** SREal: IEEE std 754 single-precision
        * "For every reading conversion, the data string sent over the bus contains the elements specified by
        the :FORMat:ELEMents command. The specified elements are sent in a particular order.
        The ASCII data format is in a direct readable form for the operator. Most BASIC languages convert
        ASCII mantissa and exponent to other formats. However, some speed is compromised to
        accommodate the conversion."
        * "REAL,32 or SREal selects the binary IEEE Std 754 single-precision data format and is shown in the
        following figure. The figure shows the normal byte order format for each data element. For example, if
        three valid elements are specified, the data string for each reading conversion is made up of three 32-
        bit data blocks. The data string for each reading conversion is preceded by a 2-byte header that is the
        binary equivalent of an ASCII # sign and 0."
        


"""

# Replace 'GPIB::24' with your instrument's address
keithley = Keithley6517B("GPIB2::27::INSTR")

keithley.write('*RST')
keithley.write(':SYST:ZCH ON')
keithley.write(':FORMAT:ELEM READ')
keithley.write(':FORMAT:DATA SRE')

# keithley.source_voltage = 1  # Sets the source voltage to 20 V
keithley.write(':SOUR:VOLT 1')

keithley.write(':SENSE:FUNC "RES"')
keithley.write(':SENSE:RES:RANGE 100e3')
keithley.write(':SENSE:RES:NPLC 0.01')
# keithley.write(':SENS:VOLT:AVERAGE:TYPE NONE')
# keithley.write(':SENS:VOLT:MED:STAT OFF')
keithley.write(':DISP:ENABLE ON')
keithley.write(':SYST:ZCH OFF')
keithley.write(':SYST:LSYNC:STAT 0')

keithley.write(':TRACE:FEED:CONT NEVER')
keithley.write(':TRACE:CLEAR')
keithley.write(':TRACE:ELEM NONE')
keithley.write(':TRACE:POINTS 100')
keithley.write(':TRIG:COUNT 100')
keithley.write(':TRIG:DELAY 0')
keithley.write(':TRACE:FEED:CONT NEXT')

keithley.write(':OUTP ON')
time.sleep(1)

keithley.write(':INIT')
time.sleep(1)

print("Buffer points: {}".format(keithley.buffer_points))
# print("resistance: {}".format(keithley.resistance))
time.sleep(2)

keithley.stop_buffer()  # Stop storing readings

# Read data from buffer
data = keithley.buffer_data
print("Buffer: {}".format(data))

print("Readings from Buffer:")
for i, reading in enumerate(data):
    print("{}: {}".format(i, reading))

keithley.write(':OUTP OFF')