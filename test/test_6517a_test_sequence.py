import os
from os.path import join
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pyvisa
import time


dict_ascii_lut = {
    'VDC': 'Volts',
    'ADC': 'Amps',
    'OHM': 'Ohms',
    'N': 'Normal',
    'Z': 'ZeroCheckEnabled',
    'O': 'Overflow',
    'U': 'Underflow',
    'R': 'Reference(Rel)',
    'L': 'OutOfLimit',
}

dict_dtypes = {
    'num': int,
    'status': str,
    'timestamp': float,
    'voltage': float,
    'measure': float,
    'units': str,
}

def parse_ascii_readings(s):
    c, u, st = [], [], []
    for x in s:
        curr, other = x.split('E')
        exp, su = other[:3], other[3:]
        curr, status, units = float(curr + 'E' + exp), su[0], su[1:]
        c.append(curr)
        u.append(dict_ascii_lut[units])
        st.append(dict_ascii_lut[status])
    return c, u, st


def parse_ascii(d, e, as_type='pd.DataFrame'):
    d = d.replace("\n", "").split(',')  # remove trailing newline character
    e = e.split(',')  # split data elements
    # - reshape
    num_vals = len(d)
    num_elem = len(e) - 2  # minus 2 because three data elements are buried within a single ','
    num_meas = num_vals // num_elem
    d = np.reshape(d, (num_meas, num_elem))
    # - get list of individual data elements
    readings = d[:, 0]
    timestamps = d[:, 1]
    reading_nums = d[:, 2]
    voltages = d[:, 3]
    # - parse
    curr, units, status = parse_ascii_readings(readings)
    timestamps = [float(x[:-4]) for x in timestamps]
    reading_nums = [int(x[:-5]) for x in reading_nums]
    voltages = [float(x[:-4]) for x in voltages]
    # - reshape
    d = np.vstack([reading_nums, status, timestamps, voltages, curr, units]).T

    if as_type == 'pd.DataFrame':
        d = pd.DataFrame(d, columns=['num', 'status', 'timestamp', 'voltage', 'measure', 'units'])
        d = d.astype(dict_dtypes)

    return d


# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------

def wrapper_6517a_test_sequence(keithley_inst, test_type, dict_sense, set_timeout, **kwargs):
    num_points = kwargs['num_points']

    # --- INITIALIZE KEITHLEY 6517a
    initialize_6517a(keithley_inst, nplc=dict_sense['nplc'], set_timeout=set_timeout)
    # -
    # --- PERFORM ZERO CORRECT
    perform_6517a_zero_correct(keithley_inst)
    # -
    # --- DEFINE TRIGGER MODEL
    setup_6517a_trigger_model(keithley_inst, num_points)
    # -
    # --- DEFINE BUFFER CONTROL
    setup_6517a_buffer_control(keithley_inst, num_points)
    # -
    # --- DEFINE SENSE FUNCTIONS
    setup_6517a_sense_functions(keithley_inst, dict_sense)
    # -
    # --- DEFINE TEST SEQUENCE
    setup_6517a_test_sequence(keithley_inst, test_type, **kwargs)
    # -
    # --- PERFORM TEST SEQUENCE and RETRIEVE DATA FROM BUFFER
    data = perform_6517a_test_sequence(keithley_inst, test_type, **kwargs)

    return data


def initialize_6517a(keithley_inst, nplc, set_timeout):
    # RESET to defaults
    keithley_inst.write('*RST')
    keithley_inst.timeout = set_timeout  # Set the timeout error time (units: ms) for PyVISA
    # --- TYPICAL SETUP
    keithley_inst.write(':FORM:DATA ASCii')  # Select data format: ASCii, REAL, SREal, DREal
    keithley_inst.write(':SYST:RNUM:RES')  # reset reading number to zero
    keithley_inst.write(':SYST:TSC OFF')  # Enable or disable external temperature readings (default: ON)
    keithley_inst.write(':SYST:HSC OFF')  # Enable or disable humidity readings (default: OFF)
    keithley_inst.write(':SYST:TST:TYPE REL')  # Configure timestamp type: RELative or RTClock
    keithley_inst.write(':TRAC:TST:FORM ABS')  # ABSolute: reference each timestamp to the first buffer reading, DELTa
    # -
    # Display: Enable/disable storage display (note, fastest data acquisition with front panel display disabled)
    if nplc < 5.0:
        keithley_inst.write(':DISP:ENAB OFF')  # Disable the front-panel display
    else:
        keithley_inst.write(':DISP:ENAB ON')  # Enable the front-panel display
    # -
    # hardware configuration
    keithley_inst.write(':SOUR:VOLT:MCON ON')  # Enable voltage source LO to ammeter LO connection (SVMI)


def setup_6517a_trigger_model(keithley_inst, num_points):
    # - Arm Layer (Arm Layer 1)
    keithley_inst.write(':INIT:CONT OFF')  # When inst returns to IDLE layer, CONT ON = repeat; OFF = hold in IDLE
    keithley_inst.write(':ARM:TCON:DIR ACCeptor')  # Wait for Arm Event (default: ACCeptor = source bypass disabled)
    keithley_inst.write(':ARM:COUN 1')  # Specify arm count: number of cycles around arm layer (default: 1)
    keithley_inst.write(':ARM:SOUR IMM')  # Select control source: IMM, TLINk, MAN or EXT. (default: IMM)
    # - Scan Layer (Arm Layer 2)
    keithley_inst.write(':ARM:LAYer2:TCON:DIR ACCeptor')  # Wait for Arm Event (ACC = source bypass disabled)
    keithley_inst.write(':ARM:LAYer2:COUN 1')  # Perform 1 arm layer cycle
    keithley_inst.write(':ARM:LAYer2:SOUR IMM')  # IMM: Immediately go to Arm Layer 2
    keithley_inst.write(':ARM:LAYer2:DEL 0')  # After receiving Arm Layer 2 Event, delay before going to Trigger Layer
    # - Measure Layer (Trigger Layer)
    print("Number of measurements in the Measure Layer: {}".format(num_points))
    keithley_inst.write(':TRIG:TCON:DIR ACC')  # Wait for trigger event (ACC = source bypass disabled)
    keithley_inst.write(':TRIG:COUN ' + str(num_points))  # Set meas count (1 to 99999 or INF) (preset: INF; Reset: 1)
    keithley_inst.write(':TRIG:SOUR IMM')  # control source (HOLD, IMMediate, TIMer, TLINk, EXTernal) (default: IMM)
    keithley_inst.write(':TRIG:DEL 0')  # After receiving Measure Event, delay before Device Action


def setup_6517a_buffer_control(keithley_inst, num_points):
    # --- Data elements in :FORM and :TRAC must match
    # NOTE: READ, STAT, RNUM, and UNIT are always enabled for the buffer and are included in the response for :ELEM?
    keithley_inst.write(
        ':FORM:ELEM READ,STAT,RNUM,UNIT,TST,VSO')  # data elements: VSOurce, READing, CHANnel, RNUMber, UNITs, TSTamp, STATus, ETEM, HUM
    keithley_inst.write(':TRAC:ELEM TST,VSO')  # data elements: TSTamp, VSOurce, CHANnel, ETEMperature, HUMidity, NONE
    # ---
    keithley_inst.write(':TRAC:CLE')  # Clear buffer
    keithley_inst.write(':TRAC:POIN:AUTO OFF')  # Disable auto buffer sizing, then size buffer
    keithley_inst.write(':TRAC:POIN ' + str(num_points))  # Specify the size of the buffer
    # Alternatively, use: keithley_inst.write(':TRAC:POIN:AUTO TRUE')  # Enable auto buffer sizing (set to measure count value in trig model)
    keithley_inst.write(':TRAC:FEED:CONT NEXT')  # Buffer control: Fill-and-stop (options: NEVer, ALWays, PRETrigger)
    # NOTE: see the "Coupled Commands" on page 331 of manual because many of these^
    # commands turn each other on or off so it's important to get the order correct.


def setup_6517a_sense_functions(keithley_inst, dict_sense):
    sense_func = dict_sense['func']
    sense_auto = dict_sense['auto']
    sense_rang = dict_sense['rang']
    sense_nplc = dict_sense['nplc']

    # always enable zero check when switching functions
    keithley_inst.write(':SYST:ZCH ON')  # Enable (ON) or disable (OFF) zero check (default: OFF)
    # -
    keithley_inst.write(':SENS:FUNC "CURR"')  # 'VOLTage[:DC]', 'CURR[:DC]', 'RES', 'CHAR' (default='VOLT:DC')
    keithley_inst.write(':SENS:CURR:NPLC ' + str(sense_nplc))  # (default=1) Set integration in line cycles (0.01 to 10)
    keithley_inst.write(':SENS:CURR:RANG:AUTO ' + sense_auto)  # Enable (ON) or disable (OFF) autorange
    keithley_inst.write(':SENS:CURR:RANG ' + str(sense_rang).upper())  # Select current range: 0 to 20e-3 (default = 20e-3)
    keithley_inst.write(':SENS:CURR:REF 0')  # Specify reference: -20e-3 to 20e-3) (default: 0)
    keithley_inst.write(':SENS:CURR:DIG 6')  # Specify measurement resolution: 4 to 7 (default: 6)
    # -
    what_range = keithley_inst.query(':SENS:CURR:RANG?')
    print("Current range: {}".format(what_range))
    # -
    # keithley_inst.write(':SYST:ZCOR:ACQ')  # Acquire zero correction value (could not get this function to work)
    # disable zero check and turn on zero correct after switching and before making measurement
    keithley_inst.write(':SYST:ZCOR ON')  # Enable (ON) or disable (OFF) zero correct (default: OFF)
    # see page 79-81 of manual for zero correct procedure



def setup_6517a_test_sequence(keithley_inst, test_type, **kwargs):
    """
    See page 210 in manual for :TSEQ programming commands.

    :param keithley_inst:
    :param test_type:
    :param kwargs:
    :return:
    """
    # --- SETUP TEST SEQUENCE
    keithley_inst.write(":TSEQ:TYPE " + test_type)  # Select the desired test sequence

    if test_type == 'SQSW':
        high_voltage_level = kwargs['high_voltage_level']
        time_at_high_level = kwargs['time_at_high_level']
        low_voltage_level = kwargs['low_voltage_level']
        time_at_low_level = kwargs['time_at_low_level']
        number_of_cycles = kwargs['number_of_cycles']

        keithley_inst.write(':SOUR:VOLT:RANG ' + str(high_voltage_level))  # range: <=100:100V, >100:1000V (default: 100 V)
        keithley_inst.write(':SOUR:VOLT:LIM ' + str(high_voltage_level))  # Define voltage limit: 0 to 1000 V (default: 1000 V)

        keithley_inst.write(":TSEQ:SQSW:HLEV " + str(high_voltage_level))  # -1000 to 1000 V
        keithley_inst.write(":TSEQ:SQSW:HTIMe " + str(time_at_high_level))  # 0 to 9999.9 s
        keithley_inst.write(":TSEQ:SQSW:LLEV " + str(low_voltage_level))  # -1000 to 1000 V
        keithley_inst.write(":TSEQ:SQSW:LTIMe " + str(time_at_low_level))  # 0 to 9999.9 s (soak time, bias time)
        keithley_inst.write(":TSEQ:SQSW:COUN " + str(number_of_cycles))  # 1 to MAX/2 (see table 2-22)
    elif test_type == 'STSW':
        start_voltage = kwargs['start_voltage']
        stop_voltage = kwargs['stop_voltage']
        step_voltage = kwargs['step_voltage']
        step_time = kwargs['step_time']

        max_voltage = np.max(np.abs(np.array([start_voltage, stop_voltage])))
        keithley_inst.write(':SOUR:VOLT:RANG ' + str(max_voltage))  # range: <=100:100V, >100:1000V (default: 100 V)
        keithley_inst.write(':SOUR:VOLT:LIM ' + str(max_voltage))  # Define voltage limit: 0 to 1000 V (default: 1000 V)

        keithley_inst.write(":TSEQ:STSW:STARt " + str(start_voltage))  # -1000 to 1000 V
        keithley_inst.write(":TSEQ:STSW:STOP " + str(stop_voltage))  # -1000 to 1000 V
        keithley_inst.write(":TSEQ:STSW:STEP " + str(step_voltage))  # -1000 to 1000 V
        keithley_inst.write(":TSEQ:STSW:STIMe " + str(step_time))  # 0 to 9999.9 s (soak time, bias time)
    elif test_type == 'CLE':
        bias_voltage = kwargs['bias_voltage']  # units: volts
        number_of_readings = kwargs['number_of_readings']  # units: integer number
        time_interval = kwargs['time_interval']  # units: seconds

        keithley_inst.write(":TSEQ:CLE:SVOL " + str(bias_voltage))  # -1000 to 1000 V
        keithley_inst.write(":TSEQ:CLE:SPO " + str(number_of_readings))  # 1 to Max Buffer Size
        keithley_inst.write(":TSEQ:CLE:SPIN " + str(time_interval))  # 0 to 99999.9 s (interval between meas. points)
    elif test_type == 'ALTP':
        offset_voltage = kwargs['offset_voltage']
        alternating_voltage = kwargs['alternating_voltage']
        measure_time = kwargs['measure_time']
        number_of_readings_to_discard = kwargs['number_of_readings_to_discard']
        number_of_readings_to_store = kwargs['number_of_readings_to_store']

        # configure resistance value that is output to buffer string
        keithley_inst.write(':SENS:RES:MSEL NORM')  # Select ohms measurement type: NORMal, RESistivity

        max_voltage = np.max(np.abs(np.array([offset_voltage, alternating_voltage])))
        keithley_inst.write(':SOUR:VOLT:RANG ' + str(
            max_voltage))  # Define voltage range: <= 100: 100V, >100: 1000 V range (default: 100 V)
        keithley_inst.write(':SOUR:VOLT:LIM ' + str(max_voltage))  # Define voltage limit: 0 to 1000 V (default: 1000 V)

        keithley_inst.write(":TSEQ:ALTP:OFSV " + str(offset_voltage))  # -1000 to 1000 V
        keithley_inst.write(":TSEQ:ALTP:ALTV " + str(alternating_voltage))  # -1000 to 1000 V
        keithley_inst.write(":TSEQ:ALTP:MTIMe " + str(measure_time))  # 0.5 to 9999.9 s (measure time)
        keithley_inst.write(":TSEQ:ALTP:DISC " + str(number_of_readings_to_discard))  # 0 to 9999
        keithley_inst.write(":TSEQ:ALTP:READ " + str(number_of_readings_to_store))  # 1 to MAX (see table 2-22)

        print("ALTP requires a minimum 0.3 second delay prior to TSEQ:TSO (starting the test).")
        # time.sleep(0.5)
        # overwrite the previous trigger source setting
        keithley_inst.write(':ARM:LAYer2:DEL 0.5')  # After receiving Arm Layer 2 Event, delay before Trigger Layer
    else:
        raise ValueError("Only 'SQSW', 'STSW', 'CLE', and 'ALTP' test are implemented.")

    keithley_inst.write(":TSEQ:TSO IMM")  # [MAN, IMM, BUS, EST, TLINK]: Select control source to start test
    # MAN: test will start when the SEQ key is pressed.
    # IMM: the test will start as soon as the :INIT command is sent, or, :INIT:CONT ON is configured.
    # BUS: the test will start when a *TRG command is sent
    # EXT: the test will start when an external trigger is received via the EXT TRIG IN connector on rear panel.
    # TLINK: the test will start when an external trigger is received via the TRIG LINK connector (:TLIN selects line)

    # - Wait for commands to complete processing
    inst_status = keithley_inst.query("*OPC?")  # see paragraph 3.11.6
    if int(inst_status) == 1:
        print("Commands have finished processed.")
    else:
        print("Commands have not finished processing.")


def perform_6517a_test_sequence(keithley_inst, test_type, **kwargs):
    # - Turn zero check off only immediately before test (i.e., after specifying all functions)
    # see page 79-81 of manual for zero correct procedure
    keithley_inst.write(':SYST:ZCH OFF')  # Enable (ON) or disable (OFF) zero check (default: OFF)
    time.sleep(0.05)
    keithley_inst.write(':SYST:ZCOR ON')  # Enable (ON) or disable (OFF) zero correct (default: OFF)
    time.sleep(0.1)
    what_zero_correct = keithley_inst.query(':SYST:ZCOR?')
    print("Zero Correct: {}".format(what_zero_correct))

    # ---

    # - Start test sequence
    keithley_inst.write("TSEQ:ARM")  # Arm the selected test sequence

    # --- Wait for buffer full (i.e., measurements done recording)
    """
    There seem to be three ways of doing this: *SRQ, *OPC?, and inputting a manual time delay (e.g., time.sleep(3))
    I have only figured out how to do the manual time delay but page 238 of the manual describes a method to use
    *OPC?, although this didn't work for me. I think because of how I set up the trigger model. 
    """
    # --- Dump buffer readings to computer CRT:
    if test_type == 'ALTP':
        num_meas = kwargs['number_of_readings_to_store']
        sleep_time = kwargs['sleep_before_read_buffer']
        sleep_dt = sleep_time / 4
        dt0 = 0
        data = ""
        for i in range(num_meas):
            dt = 0
            for j in range(4):
                time.sleep(sleep_dt)
                dt += sleep_dt
                dt0 += sleep_dt
                print("Time elapsed: {} s/meas, {} s total".format(dt, dt0))
            datum = keithley_inst.query(":TRAC:LAST?")
            print(datum)
            if i == 0:
                data = datum.replace("\n", "")
            else:
                data = "{},{}".format(data, datum.replace("\n", ""))
    else:
        data = keithley_inst.query(":TRAC:DATA?")
        print(data)

    return data


def perform_6517a_zero_correct(keithley_inst):
    # see page 79-81 of manual for zero correct procedure (example on page 57)
    keithley_inst.write(':SYST:ZCH ON')  # Enable (ON) or disable (OFF) zero check (default: OFF)
    # Set up Source functions
    keithley_inst.write(':SOUR:VOLT 0')  # Define voltage level: -1000 to +1000 V (default: 0)
    keithley_inst.write(':SOUR:VOLT:RANG 1000')  # <100=100V, >100=1000V
    keithley_inst.write(':SOUR:VOLT:LIM 1000')  # Define voltage limit: 0 to 1000 V (default: 1000 V)
    # Set up Sense functions
    keithley_inst.write(':SENS:FUNC "CURR"')  # 'VOLTage[:DC]', 'CURRent[:DC]', 'RESistance', 'CHARge' (default='VOLT:DC')
    keithley_inst.write(':SENS:CURR:RANG:AUTO OFF')  # Enable (ON) or disable (OFF) autorange
    keithley_inst.write(':SENS:CURR:RANG 2E-12')  # Select current range: 0 to 20e-3 (default = 20e-3)
    # k3.write(':SENS:CURR:REF 0')  # Specify reference: -20e-3 to 20e-3) (default: 0)
    keithley_inst.write(':SYST:ZCH OFF')  # Enable (ON) or disable (OFF) zero check (default: OFF)
    # Execute configured measurement
    keithley_inst.write('OUTP ON')  # Turn source ON
    # k3.write(':INIT')  # Move from IDLE state to ARM Layer 1
    # k3.write(':SOUR:VOLT 0')  # Set voltage level to 0
    time.sleep(0.5)
    keithley_inst.write(':SYST:ZCOR:ACQ')  # Acquire zero correction value (could not get this function to work)
    time.sleep(0.5)
    # keithley_inst.write(':SYST:ZCOR ON')  # Enable (ON) or disable (OFF) zero correct (default: OFF)
    keithley_inst.write(':OUTP OFF')  # turn output off
    keithley_inst.write(':SYST:ZCH ON')  # Enable (ON) or disable (OFF) zero check (default: OFF)


if __name__ == "__main__":
    """
    Buffer readings:
        * Max reading rate to internal buffer: 125 readings/second (NPLC=0.01, front panel off, temperature + RH off)
            ** The reading interval (time between readings) is more uniform with front panel off)
        * Max buffer readings (i.e., size): including additional elem[TIMESTAMP, VSOURCE] is 8566
        * NOTE: READ, STAT, RNUM, and UNIT are always enabled for the buffer and are included in the response for :ELEM?

    SPECS:
        * Volts (see page 312 in manual):
            ** range 2V: 10 uV resolution
            ** range 20V: 100 uV resolution
            ** range 200V: 1 mV resolution
            ** Input impedance > 200 TeraOhms (10 MOhms with zero check on)
        * Amps:
            ** range 2nA: 10 femtoAmp resolution (assumes NPLC=1 and median filtering of 10 readings)
            ** 20 nA: 100 fA
            ** 200 nA: 1 pA
            ** 2 uA: 10 pA
            ** 20 uA: 100 pA
            ** 200 uA: 1 nA
        * Ohms:
            ** range 200 MOhms: 1 kOhm resolution (Auto V Source: 40 V; Amps range: 2 uA)
            ** 2 GOhms: 10 kOhms
            ** 20 GOhms: 100 kOhms
    """
    # Quasi Limits
    max_buffer = 8566  # assumes timestamp and voltage included in data elements.

    #TODO:
    """
    1. The timeout is currently determined by NPLC, but the actual minimum sampling time is more like 35 ms. 
        So, the timeout should be set to whichever is a longer time (NPLC or 35 ms). 
    2. It would be very helpful if I didn't need to change the number for each test. 
        The script should search the save directory, find all similar files, identify the highest number,
        and automatically increment the number. 
    """

    # --- SETUP
    rm = pyvisa.ResourceManager()
    check_inst = False  # True False
    if check_inst is True:
        print(rm.list_resources())  # only list "::INSTR" resources
        # # returns something like: ('ASRL1::INSTR', 'ASRL2::INSTR', 'GPIB0::14::INSTR')
        raise ValueError("Check instruments are connected.")
    # open instrument
    k1_source_GPIB, k1_source_board_index = 24, 0  # Keithley 6517a electrometer
    k1 = rm.open_resource('GPIB{}::{}::INSTR'.format(k1_source_board_index, k1_source_GPIB))

    # ---
    # -
    # setup base directory
    base_dir = r'C:\Users\nanolab\Box\2024\zipper_paper\Methods\I-V-Resistance Measurements'
    # -
    test_subject_id = 'C10-20pT_25nmAu'
    save_dir = os.path.join(base_dir, test_subject_id)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    # -
    # specify test sequence: SQSW, STSW, CLE, ALTP
    test_type = 'ALTP'
    save_id = '{}_test1'.format(test_type)
    dict_sense = {
        'func': "CURR",
        'auto': 'OFF',  # ON OFF
        'rang': 20E-3,  # (200 pA, 20 mA)
        'nplc': 10,  # (0.01, 10): if NPLC < 1.0, then front panel display is disabled for speed
    }  # You can set both a CURR:RANG and AUTO:ON, then RANG defines the upper-bound to seek optimal range.
    integration_period = dict_sense['nplc'] / 60
    print("Integration period = {} ms".format(np.round(integration_period * 1000)))
    # FLASHING VOLTAGE SOURCE LIGHT
    """
    A flashing VOLTAGE SOURCE OPERATE
    LED indicates that the V-Source has
    gone into current limit. The programmed
    voltage is not being applied to the load. In
    this situation, try using a lower voltage for
    the measurement.
    """
    # -
    # perform test
    if test_type == 'SQSW':
        """
        NOTES:
        From the speed test:
            * it seems that 20 ms is the shortest 'acceptable' dwell time. 
                Shorter dwell times don't actually lead to shorter total times and may actually
                mess out the data output (which is what I saw for a dwell time of 10 ms). However,
                there is a significant asymmetry in the +V and -V dwell times for even 20 ms. 
                On average: switching to -V takes 35 ms; switching to +V takes 72 ms. 
            * Using 100 ms dwell time:
                On average: switching to -V takes 116 ms; switching to +V takes 158 ms.
            * Conclusion: 
                It seems the asymmetric switching time is quasi-constant. 
        """
        shortest_time = integration_period * 2
        # inputs
        high_voltage_level = 0.5  # -1000 to 1000 volts (default: 1)
        time_at_high_level = shortest_time  # 0 to 9999.9 seconds (default: 1)
        low_voltage_level = -0.5  # -1000 to 1000 volts (default: -1)
        time_at_low_level = shortest_time  # 0 to 9999.9 seconds (default: 1)
        number_of_cycles = 50  # positive integer
        # -
        # derived inputs
        num_points = number_of_cycles * 2
        cycle_time = time_at_high_level + time_at_low_level
        total_time = cycle_time * number_of_cycles
        # set PyVisa timeout
        estimated_timeout = (total_time * 3.5) * 1000 * 3  # (ms)
        # --- export settings
        dict_settings = {
            'high_voltage_level': high_voltage_level,
            'time_at_high_level': time_at_high_level,
            'low_voltage_level': low_voltage_level,
            'time_at_low_level': time_at_low_level,
            'number_of_cycles': number_of_cycles,
            'num_points': num_points,
            'cycle_time': cycle_time,
            'total_time': total_time,
        }
        dict_settings.update(dict_sense)
        # -
        # --- Perform test sequence
        data = wrapper_6517a_test_sequence(
            keithley_inst=k1,
            test_type=test_type,
            dict_sense=dict_sense,
            set_timeout=estimated_timeout,
            high_voltage_level=high_voltage_level,
            time_at_high_level=time_at_high_level,
            low_voltage_level=low_voltage_level,
            time_at_low_level=time_at_low_level,
            number_of_cycles=number_of_cycles,
            num_points=num_points,
        )
    elif test_type == 'STSW':
        """
        Notes from speed test:
            * Using a step time of 10 ms, the actual step time was 70 ms (same for +V or -V). 
        """
        shortest_time = integration_period * 1.5
        # inputs
        start_voltage = -0.5  # volts (default: 1)
        stop_voltage = 0.5  # volts (default: 10)
        step_voltage = 0.05  # volts (default: 1)
        step_time = shortest_time  # seconds (default: 1)
        # -
        # derived inputs
        num_points = int(np.round((stop_voltage - start_voltage) / step_voltage)) + 1
        # set PyVisa timeout
        estimated_timeout = (num_points * step_time * 3) * 1000  # (ms)
        # --- export settings
        dict_settings = {
            'start_voltage': start_voltage,
            'stop_voltage': stop_voltage,
            'step_voltage': step_voltage,
            'step_time': step_time,
            'num_points': num_points,
        }
        dict_settings.update(dict_sense)
        # -
        # --- Perform test sequence
        data = wrapper_6517a_test_sequence(
            keithley_inst=k1,
            test_type=test_type,
            dict_sense=dict_sense,
            set_timeout=estimated_timeout,
            start_voltage=start_voltage,
            stop_voltage=stop_voltage,
            step_voltage=step_voltage,
            step_time=step_time,
            num_points=num_points,
        )
    elif test_type == 'CLE':
        """
        Notes from speed test:
            * Using a time interval of 0.01, the actual per-sample time was 15 ms (which agrees with specified time).
        """
        bias_voltage = 0.5  # volts (default: 1)
        number_of_readings = 50  # integer number (default: 10)
        time_interval = integration_period * 1.25  # seconds (default: 1)
        # set PyVisa timeout
        estimated_timeout = (number_of_readings * time_interval * 3.5) * 1000  # (ms)
        # --- export settings
        dict_settings = {
            'bias_voltage': bias_voltage,
            'number_of_readings': number_of_readings,
            'time_interval': time_interval,
            'num_points': number_of_readings,
        }
        dict_settings.update(dict_sense)
        # -
        # --- Perform test sequence
        data = wrapper_6517a_test_sequence(
            keithley_inst=k1,
            test_type=test_type,
            dict_sense=dict_sense,
            set_timeout=estimated_timeout,
            bias_voltage=bias_voltage,
            number_of_readings=number_of_readings,
            time_interval=time_interval,
            num_points=number_of_readings,
        )
    elif test_type == 'ALTP':
        """
        see page 316 of manual for method to calculate accuracy and repeatability of ATLP method
        """
        offset_voltage = 0  # volts (default: 0 V)
        alternating_voltage = 0.5  # volts (default: 10 V)
        measure_time = 3  # seconds (default: 15 s)
        # dwell time at each voltage (i.e., +V for 15 s, -V for 15 s, +V for 15 s, etc.)
        # NOTE: measure_time should be at least 15 seconds for 200 pA range or less.
        number_of_readings_to_discard = 3  # (default: 3)
        number_of_readings_to_store = 1  # (default: 1)
        # -
        # set PyVisa timeout
        estimated_meas_time = \
            ((number_of_readings_to_discard + number_of_readings_to_store + 4) * measure_time)  # (s)
        sleep_before_read_buffer = estimated_meas_time * 1.1
        estimated_timeout = number_of_readings_to_store * estimated_meas_time * 1.5 * 1000
        print("Sleep time before read buffer: {} s".format(sleep_before_read_buffer))
        print("PyVISA timeout set to: {} s".format(estimated_timeout / 1000))
        # --- export settings
        dict_settings = {
            'offset_voltage': offset_voltage,
            'alternating_voltage': alternating_voltage,
            'measure_time': measure_time,
            'number_of_readings_to_discard': number_of_readings_to_discard,
            'number_of_readings_to_store': number_of_readings_to_store,
            'num_points': number_of_readings_to_store,
            'sleep_before_read_buffer': sleep_before_read_buffer,
        }
        dict_settings.update(dict_sense)
        # -
        # --- Perform test sequence
        data = wrapper_6517a_test_sequence(
            keithley_inst=k1,
            test_type=test_type,
            dict_sense=dict_sense,
            set_timeout=estimated_timeout,
            offset_voltage=offset_voltage,
            alternating_voltage=alternating_voltage,
            measure_time=measure_time,
            number_of_readings_to_discard=number_of_readings_to_discard,
            number_of_readings_to_store=number_of_readings_to_store,
            num_points=number_of_readings_to_store,
            sleep_before_read_buffer=sleep_before_read_buffer,
        )
        # NOTE: use command :TRAC:LAST? to read the last reading stored in buffer (applies only to ALTP test)
    else:
        raise ValueError("Only 'SQSW', 'STSW', 'CLE', and 'ALTP' test are implemented.")
    # -
    # --- UNKNOWN HOW IMPORTANT THIS IS
    # k3.close()  # close instrument
    # -
    # --- parse, package, and export
    data_elements = k1.query(':FORMat:ELEM?')
    df = parse_ascii(d=data, e=data_elements, as_type='pd.DataFrame')
    df_settings = pd.DataFrame.from_dict(data=dict_settings, orient='index')

    file = join(save_dir, '{}_data.xlsx'.format(save_id))
    sns, dfs = ['data', 'settings'], [df, df_settings]
    idx, lbls = [False, True], [None, 'k']
    with pd.ExcelWriter(file) as writer:
        for sheet_name, dataframe, idx, idx_lbl in zip(sns, dfs, idx, lbls):
            dataframe.to_excel(writer, sheet_name=sheet_name, index=idx, index_label=idx_lbl)

    # --- PLOTTING

    # setup
    # df.columns = ['num', 'status', 'timestamp', 'voltage', 'measure', 'units']
    measure_units = df['units'].iloc[0]

    dt = df['timestamp'].iloc[-1]
    num_samples = len(df)
    samples_per_second = num_samples / dt
    print("{} samples / {} s = {} samples/s".format(num_samples, dt, samples_per_second))

    fig, (ax1, ax2, ax3) = plt.subplots(nrows=3, figsize=(10, 10))

    ax1.plot(df['timestamp'], df['measure'], '-o', label=samples_per_second)
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel(measure_units)
    ax1.grid(alpha=0.2)
    ax1.legend(title='#/s', loc='upper right', fontsize='small')

    ax2.plot(df['timestamp'], df['voltage'], '-o')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Voltage (V)')
    ax2.grid(alpha=0.2)

    ax3.plot(df['voltage'], df['measure'], '-o')
    ax3.set_xlabel('Voltage (V)')
    ax3.set_ylabel(measure_units)
    ax3.grid(alpha=0.2)

    plt.suptitle(save_id)
    plt.tight_layout()
    plt.savefig(join(save_dir, 'fig_{}.png'.format(save_id)), dpi=300, facecolor='w', bbox_inches='tight')
    plt.show()
    plt.close()

    print("Completed without errors.")
