from pymeasure.instruments.keithley import Keithley6517B
from time import sleep
import time

# Replace 'GPIB::24' with your instrument's address
keithley = Keithley6517B("GPIB2::27::INSTR")

pymeasure_example = False
if pymeasure_example:
    #keithley.apply_voltage()  # Sets up to source current
    #keithley.source_voltage_range = 20  # Sets the source voltage

    # range to 200 V
    keithley.source_voltage = 0.1  # Sets the source voltage to 20 V
    keithley.enable_source()  # Enables the source output
    keithley.write(':SYST:ZCH OFF')

    keithley.measure_resistance(nplc=10, auto_range=True)  # Sets up to measure resistance

    keithley.ramp_to_voltage(10)  # Ramps the voltage to 50 V
    print(keithley.resistance)  # Prints the resistance in Ohms
    sleep(1)

    keithley.shutdown()  # Ramps the voltage to 0 V
    # and disables output
    raise ValueError()


chatgpt_example = False
if chatgpt_example:
    # try:
    keithley.reset()

    #keithley.measure_resistance()  # Configure to measure resistance, change as needed
    #keithley.resistance_nplc = 1  # Set NPLC
    #keithley.reset_buffer()  # Clear buffer
    #keithley.enable_buffer()  # Enable buffer
    #keithley.start_buffer()  # Start storing readings in buffer

    #keithley.config_buffer(points=64, delay=0.25)
    keithley.write(":STAT:PRES")
    keithley.write("*CLS")
    keithley.write("*SRE 1")
    keithley.write(":STAT:MEAS:ENAB 512")
    keithley.write(":TRAC:CLEAR")

    keithley.buffer_points = 64
    keithley.trigger_count = 64
    keithley.trigger_delay = 0.2
    #keithley.write(":TRAC:FEED SENSE")

    keithley.write(":TRAC:FEED:CONT NEXT")
    keithley.trigger_on_bus()

    keithley.check_errors()

    print("sleep before start")
    time.sleep(2)
    print("starting")


    # keithley.measure_resistance(nplc=1, auto_range=True)  # Sets up to measure resistance
    keithley.measure_current(nplc=1, auto_range=True)
    keithley.source_voltage = 1  # Sets the source voltage to 20 V
    keithley.write(':SYST:ZCH OFF')


    keithley.enable_source()  # Enables the source output
    keithley.start_buffer()

    # def wait_for_buffer(self, should_stop=lambda: False, timeout=60, interval=0.1):
    wait_for_buf = False
    if wait_for_buf:
        timeout = 3
        interval = 0.25
        should_stop = lambda: False
        """ Blocks the program, waiting for a full buffer. This function
        returns early if the :code:`should_stop` function returns True or
        the timeout is reached before the buffer is full.
    
        :param should_stop: A function that returns True when this function should return early
        :param timeout: A time in seconds after which this function should return early
        :param interval: A time in seconds for how often to check if the buffer is full
        """
        # TODO: Use SRQ initially instead of constant polling
        # self.adapter.wait_for_srq()
        t = time.time()
        while not keithley.is_buffer_full():
            sleep(interval)
            if should_stop():
                pass
            elif (time.time() - t) > timeout:
                # raise Exception("Timed out waiting for Keithley buffer to fill.")
                pass
            else:
                print(time.time() - t)

    # Take readings for a while
    for i in range(5):
        print("reading a {}".format(i))
        sleep(1)  # Wait 1 second
        print("reading b {}".format(i))
        # keithley.trigger()  # Trigger a reading
        keithley.measure_current(nplc=1, auto_range=True)
        print(keithley.current)
        print("reading c {}".format(i))

    keithley.stop_buffer()  # Stop storing readings

    # Read data from buffer
    data = keithley.buffer_data
    print("Readings from Buffer:")
    for reading in data:
        print(reading)

    #except Exception as e:
    #    print(f"An error occurred: {e}")

    #finally:
    #    keithley.disable_buffer()
    keithley.adapter.connection.close()

forums_ni_example = True
""" NOTE: The following program works!!! It reads data from the buffer! """
if forums_ni_example:
    """
    REF: https://forums.ni.com/t5/Instrument-Control-GPIB-Serial/Help-reading-buffer-in-Keithley-Electrometer-6517B-through-SCPI/td-p/4356861
    
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
    """
    keithley.write('*RST')
    keithley.write(':SYST:ZCH ON')
    keithley.write(':FORMAT:ELEM READ')
    keithley.write(':FORMAT:DATA SRE')

    # keithley.source_voltage = 1  # Sets the source voltage to 20 V
    keithley.write(':SOUR:VOLT 1')

    keithley.write(':SENSE:FUNC "RES"')
    keithley.write(':SENSE:RES:RANGE 100e3')
    keithley.write(':SENSE:RES:NPLC 0.01')
    #keithley.write(':SENS:VOLT:AVERAGE:TYPE NONE')
    #keithley.write(':SENS:VOLT:MED:STAT OFF')
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