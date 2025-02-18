from os.path import join
import os
from pymeasure.instruments.keithley import Keithley6517B
import time






if __name__ == "__main__":

    # --- HARDWARE SETUP
    # Keithley 6517 electrometer used as voltage source and coulomb meter
    K1_BOARD_INDEX, K1_GPIB, K1_INST = 2, 27, '6517b'

    # ---

    # root test subject
    BASE_DIR = r'C:\Users\nanolab\Box\2024\zipper_paper\Methods\CapacitanceMeasurements'
    TEST_TYPE = 'CAPACITANCE'
    TEST_SUBJECT = '1nF'
    # ---
    TID = 1
    SOURCE_VOLTAGE = 10  # voltage
    SENSE_FUNC = 'CHAR'  # 'RES', 'CURR', 'CHAR'
    SENSE_NPLC = 1  # 0.01 to 10
    SENSE_NUM_SAMPLES = 100
    #SENSE_USE_REFERENCE = None  # 'CHAR', 'ZCOR', or None
    #SENSE_RANGE_AUTO = 'OFF'
    SENSE_RANGE = 2e-6  # Coulombs: 0 to 2e6

    # ---
    SAVE_ID = 'tid{}_{}V_{}NPLC_test-{}'.format(TID, SOURCE_VOLTAGE, SENSE_NPLC, TEST_TYPE)
    SAVE_DIR = join(BASE_DIR, TEST_SUBJECT)
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    # Replace 'GPIB::24' with your instrument's address
    keithley = Keithley6517B("GPIB{}::{}::INSTR".format(K1_BOARD_INDEX, K1_GPIB))

    keithley.write('*RST')
    keithley.write(':SYST:ZCH ON')
    keithley.write(':FORMAT:ELEM READ')  # Store only the reading
    keithley.write(':FORMAT:DATA SRE')  # SREal: IEEE std 754 single-precision

    keithley.write(':SOUR:VOLT ' + str(SOURCE_VOLTAGE))

    if SENSE_FUNC == 'CHAR':
        keithley.write(':SENSE:FUNC "{}"'.format(SENSE_FUNC))
        keithley.write(':SENSE:CHAR:RANGE {}' + str(SENSE_RANGE))
        keithley.write(':SENSE:CHAR:NPLC {}' + str(SENSE_NPLC))
    elif SENSE_FUNC == 'CURR':
        keithley.write(':SENSE:FUNC "{}"'.format(SENSE_FUNC))
        keithley.write(':SENSE:CURR:RANGE {}' + str(SENSE_RANGE))
        keithley.write(':SENSE:CURR:NPLC {}' + str(SENSE_NPLC))
    elif SENSE_FUNC == 'VOLT':
        keithley.write(':SENSE:FUNC "{}"'.format(SENSE_FUNC))
        keithley.write(':SENSE:VOLT:RANGE {}' + str(SENSE_RANGE))
        keithley.write(':SENSE:VOLT:NPLC {}' + str(SENSE_NPLC))
    elif SENSE_FUNC == 'RES':
        keithley.write(':SENSE:FUNC "{}"'.format(SENSE_FUNC))
        keithley.write(':SENSE:RES:RANGE {}' + str(SENSE_RANGE))
        keithley.write(':SENSE:RES:NPLC {}' + str(SENSE_NPLC))
    else:
        raise ValueError("Sense function not understood.")
    #keithley.write(':SENS:VOLT:AVERAGE:TYPE NONE')
    #keithley.write(':SENS:VOLT:MED:STAT OFF')
    keithley.write(':DISP:ENABLE OFF')  # originally, ON
    keithley.write(':SYST:ZCH OFF')
    keithley.write(':SYST:LSYNC:STAT 0')  # disable power line synchronization

    keithley.write(':TRACE:FEED:CONT NEVER')  # disable buffer reading
    keithley.write(':TRACE:CLEAR')  # clear buffer
    keithley.write(':TRACE:ELEM NONE')  # data store elements: NONE
    keithley.write(':TRACE:POINTS ' + str(SENSE_NUM_SAMPLES))
    keithley.write(':TRIG:COUNT ' + str(SENSE_NUM_SAMPLES))
    keithley.write(':TRIG:DELAY 0')
    keithley.write(':TRACE:FEED:CONT NEXT')  # specify buffer control: fill and stop.

    keithley.write(':OUTP ON')
    time.sleep(1)

    keithley.write(':INIT')
    time.sleep(1)

    print("Buffer points: {}".format(keithley.buffer_points))
    # print("resistance: {}".format(keithley.resistance))
    time.sleep(2)

    keithley.stop_buffer()  # Stop storing readings
    """ Aborts the buffering measurement, by stopping the measurement
    arming and triggering sequence. """
    # self.write(":ABOR")

    second_pass_modifiers = False
    if second_pass_modifiers:
        # NOTE: READ, STAT, RNUM, and UNIT are always enabled for the buffer and are included in the response for :ELEM?
        keithley.write(':FORM:ELEM READ,STAT,RNUM,UNIT,TST,VSO')  # data elements

    # Read data from buffer
    data = keithley.buffer_data
    """ Get a numpy array of values from the buffer. """
    #self.write(":FORM:DATA ASCII")
    #return np.array(self.values(":TRAC:DATA?"), dtype=np.float64)
    print("Buffer: {}".format(data))

    print("Readings from Buffer:")
    for i, reading in enumerate(data):
        print("{}: {}".format(i, reading))


    keithley.write(':SOUR:VOLT 0')
    time.sleep(5)
    keithley.write(':OUTP OFF')