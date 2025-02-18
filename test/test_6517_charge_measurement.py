import os
from os.path import join
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pyvisa
import time


def setup_6517_initialize(keithley_inst, settings):
    # 2. SYSTEM
    keithley_inst.write(':SYST:RNUM:RES')  # reset reading number to zero
    keithley_inst.write(':SYST:TSC OFF')  # Enable or disable external temperature readings (default: ON)
    keithley_inst.write(':SYST:TST:TYPE REL')  # Configure timestamp type: RELative or RTClock
    keithley_inst.write(':FORM:DATA ASCii')  # Select data format: ASCii, REAL, SREal, DREal

    # --- Define Trigger Model
    keithley_inst.write(':INIT:CONT OFF')  # When return to IDLE layer, CONTINUOUS ON = repeat; OFF = hold in IDLE
    keithley_inst.write(':ARM:TCON:DIR ACCeptor')  # Wait for Arm Event (default: ACCeptor)
    keithley_inst.write(':ARM:COUN 1')  # Specify arm count: number of cycles around arm layer (default: 1)
    keithley_inst.write(':ARM:SOUR IMM')  # Select control source: IMM, TLINk or EXT. (default: IMM)
    # -
    keithley_inst.write(':ARM:LAYer2:TCON:DIR ACCeptor')  # Wait for Arm Event
    keithley_inst.write(':ARM:LAYer2:COUN 1')  # Perform 1 arm layer cycle
    keithley_inst.write(':ARM:LAYer2:SOUR IMM')  # Immediately go to Arm Layer 2
    keithley_inst.write(':ARM:LAYer2:DEL 0')  # After receiving Arm Layer 2 Event, delay before going to Trigger Layer
    # -
    keithley_inst.write(':TRIG:TCON:DIR ACC')  # Wait for trigger event
    keithley_inst.write(':TRIG:COUN ' + str(settings['sense_num_samples']))  # Set measure count (1 to 99999 or INF)
    keithley_inst.write(':TRIG:SOUR IMM')  # Select control source (HOLD, IMMediate, TIMer, MANual) (default: IMM)

    if settings['buffer_control'] == 'NEXT':
        settings = setup_6517a_buffer_control(keithley_inst, settings)
    elif settings['buffer_control'] == 'NEV':
        keithley_inst.write(':TRAC:FEED:CONT NEV')  # disable buffer control
        keithley_inst.write(
            ':FORM:ELEM READ,TST,VSO')  # data elements: VSOurce, READing, RNUMber, UNITs, TSTamp, STATus
    else:
        raise ValueError("Buffer control not understood. Options are: ['NEXT', 'NEV'].")
    return settings


def setup_6517a_buffer_control(keithley_inst, settings):
    # --- Data elements in :FORM and :TRAC must match
    # NOTE: READ, STAT, RNUM, and UNIT are always enabled for the buffer and are included in the response for :ELEM?
    keithley_inst.write(
        ':FORM:ELEM READ,STAT,RNUM,UNIT,TST,VSO')  # data elements: VSOurce, READing, CHANnel, RNUMber, UNITs, TSTamp, STATus, ETEM, HUM
    keithley_inst.write(':TRAC:ELEM TST,VSO')  # data elements: TSTamp, VSOurce, CHANnel, ETEMperature, HUMidity, NONE
    # ---
    keithley_inst.write(':TRAC:CLE')  # Clear buffer
    if settings['buffer_size_auto'] == 'ON':
        keithley_inst.write(':TRAC:POIN:AUTO ON')  # Enable auto buffer sizing (set to measure count in trig model)
        buffer_size = keithley_inst.query(':TRAC:POIN?')
        print("Buffer size (AUTO): {} ".format(buffer_size))
        settings.update({'buffer_size': buffer_size})
    else:
        keithley_inst.write(':TRAC:POIN:AUTO OFF')  # Disable auto buffer sizing, then size buffer
        keithley_inst.write(':TRAC:POIN ' + str(settings['buffer_size']))  # Specify the size of the buffer
    # Alternatively, use:
    keithley_inst.write(':TRAC:FEED:CONT NEXT')  # Buffer control: Fill-and-stop (options: NEVer, ALWays, PRETrigger)
    # NOTE: see the "Coupled Commands" on page 331 of manual because many of these^
    # commands turn each other on or off so it's important to get the order correct.
    return settings


def setup_6517_source_voltage_measure_charge(keithley_inst, settings):
    # Source: VOLTage
    keithley_inst.write(':SOUR:VOLT:MCON OFF')
    keithley_inst.write(':SOUR:VOLT:RANG ' + str(settings['source_voltage']))
    keithley_inst.write(':SOUR:VOLT ' + str(settings['source_voltage']))

    keithley_inst.write(':SYST:ZCH ON')  # Enable (ON) or disable (OFF) zero check (default: OFF)

    # Sense: CHARge
    keithley_inst.write(':SENS:FUNC "CHAR"')  # 'CHARge'
    keithley_inst.write(':CHAR:NPLC ' + str(settings['sense_nplc']))  # NPLC: 0.01 to 10
    keithley_inst.write(':CHAR:RANG ' + str(settings['sense_range']))  # RANGe: 0 to 2e-6
    keithley_inst.write(':CHAR:RANG:AUTO ' + str(settings['sense_range_auto']))  # OFF or ON

    keithley_inst.write(':CHAR:AVER OFF')  # Disable averaging filter
    keithley_inst.write(':CHAR:MED OFF')  # Disable median filter
    keithley_inst.write(':CHAR:ADIS OFF')  # Disable autodischarge


def setup_6517_reference(keithley_inst, settings):
    if settings['sense_use_reference'] is None:
        reference_value = 'None'
        keithley_inst.write(':SYST:ZCH OFF')
    elif settings['use_reference'] == 'CHAR':
        # print reference value
        reference_value = keithley_inst.query(':CHAR:REF?')
        print("Reference Value (INCOMING): {}".format(reference_value))
        # disable zero check
        keithley_inst.write(':SYST:ZCH OFF')
        # allow charge to dissipate
        time.sleep(2)
        # acquire reference value
        keithley_inst.write(':CHAR:REF:ACQ')  # use input signal as reference
        # print new reference value
        reference_value = keithley_inst.query(':CHAR:REF?')
        print("Reference Value (post-ACQuire): {}".format(reference_value))
        # enable reference for Coulombs
        keithley_inst.write(':CHAR:REF:STAT ON')
    elif settings['sense_use_reference'] == 'ZCOR':
        if keithley_inst.query(':SYST:ZCH?') == 0:
            keithley_inst.write(':SYST:ZCH ON')
        keithley_inst.write(':SYST:ZCOR:ACQ')
        keithley_inst.write(':SYST:ZCOR ON')
        reference_value = 'n/a'
        # disable zero check
        keithley_inst.write(':SYST:ZCH OFF')
    else:
        raise ValueError("use_reference can only be: None, 'CHAR', or 'ZCOR'.")
    settings.update({'sense_reference_value': reference_value})
    return settings


def calculate_capacitance(q1, q2, v1, v2):
    return (q2 - q1) / (v2 - v1)


# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    """
    Capacitance Measurements (pg. 190 of Keithley Low Level measurement handbook, 7th edition)
    Procedure:
        0. Setup Meter Connect configuration (MCON) and charge measurement
        1. Disable zero check and use "REL" function to zero the charge
        2. Turn on voltage source 
        3. Note the charge reading immediately
        4. Calculate capacitance: C = (Q2 - Q1) / (V2 - V1)
            where 
                Q2 is the charge reading, 
                Q1 should be zero (because REL function zeroes the charge),
                V2 is the step voltage,
                V1 should be zero (because we initially did not apply a voltage).
        5. Reset voltage source to 0V to dissipate charge from the capacitor. 

    """

    # --- HARDWARE SETUP
    # available instruments
    rm = pyvisa.ResourceManager()
    check_inst = True  # True False
    if check_inst is True:
        print(rm.list_resources())  # only list "::INSTR" resources
        raise ValueError("Check instruments are connected.")
    # instrument addresses
    # Keithley 6517 electrometer used as voltage source and coulomb meter
    K1_GPIB, K1_BOARD_INDEX, K1_INST = 27, 2, '6517b'

    # ---

    # root test subject
    BASE_DIR = r'C:\Users\nanolab\Desktop\test'
    TEST_TYPE = 'CAPACITANCE'
    TEST_SUBJECT = '500nF'
    # ---
    TID = 1
    SOURCE_VOLTAGE = 50  # max bipolar: 350 V; max unipolar: 700 V
    SENSE_NPLC = 0.25  # 0.01 to 10
    SENSE_NUM_SAMPLES = 1000
    SENSE_USE_REFERENCE = 'CHAR'  # 'CHAR' or 'ZCOR'
    SENSE_RANGE = 2e-6  # Coulombs: 0 to 2e6
    SENSE_RANGE_AUTO = 'OFF'
    # ---
    BUFFER_CONTROL = 'NEXT'  # 'NEXT' or 'NEV'
    BUFFER_SIZE_AUTO = 'ON'  # 'ON' or 'OFF'

    # ---
    SAVE_ID = 'tid{}_{}V_ref{}_{}NPLC_test-{}'.format(TID, SOURCE_VOLTAGE, SENSE_USE_REFERENCE, SENSE_NPLC, TEST_TYPE)
    SAVE_DIR = join(BASE_DIR, TEST_SUBJECT)
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    # ---

    if TID is not None:
        SENSE_INTEGRATION_PERIOD = SENSE_NPLC / 60
        SLEEP_BEFORE_READ_BUFFER = SENSE_NUM_SAMPLES * SENSE_INTEGRATION_PERIOD * 1.2
        ESTIMATED_TIMEOUT = SLEEP_BEFORE_READ_BUFFER * 1.2
        DICT_SETTINGS = {
            'tid': TID,
            'save_dir': SAVE_DIR,
            'save_id': SAVE_ID,
            'test_type': TEST_TYPE,
            'source_inst': K1_INST,
            'source_voltage': SOURCE_VOLTAGE,
            'sense_inst': K1_INST,
            'sense_num_samples': SENSE_NUM_SAMPLES,
            'sense_nplc': SENSE_NPLC,
            'sense_integration_period': SENSE_INTEGRATION_PERIOD,
            'sense_use_reference': SENSE_USE_REFERENCE,
            'sense_range': SENSE_RANGE,
            'sense_range_auto': SENSE_RANGE_AUTO,
            'buffer_control': BUFFER_CONTROL,
            'buffer_size_auto': BUFFER_SIZE_AUTO,
            'sleep_before_read_buffer': SLEEP_BEFORE_READ_BUFFER,
            'pyvisa_estimated_timeout': ESTIMATED_TIMEOUT,
        }
        if BUFFER_CONTROL == 'NEXT' and 'BUFFER_SIZE_AUTO' == 'OFF':
            BUFFER_SIZE = SENSE_NUM_SAMPLES * 7
            DICT_SETTINGS.update({'buffer_size': BUFFER_SIZE})

    # ---

    # open instrument
    k1 = rm.open_resource('GPIB{}::{}::INSTR'.format(K1_GPIB, K1_BOARD_INDEX))
    k1.write('*RST')
    k1.timeout = DICT_SETTINGS['pyvisa_estimated_timeout'] * 1000  # Set the timeout error time (units: ms) for PyVISA

    # 0. Setup charge measurement function
    DICT_SETTINGS = setup_6517_initialize(keithley_inst=k1, settings=DICT_SETTINGS)
    setup_6517_source_voltage_measure_charge(keithley_inst=k1, settings=DICT_SETTINGS)

    # 1. Zero charge immediately before measure
    DICT_SETTINGS = setup_6517_reference(keithley_inst=k1, settings=DICT_SETTINGS)

    # 2. Turn on voltage source (i.e., apply a step voltage)
    # 3. Measure charge immediately after voltage step
    k1.write(':SYST:TST:REL:RES')  # Reset relative timestamp to 0.
    k1.write(':OUTP ON')
    k1.write(':INIT')
    time.sleep(DICT_SETTINGS['sleep_before_read_buffer'])
    data = k1.query(":TRAC:DATA?")
    data_elements = k1.query(':FORMat:ELEM?')
    print(data)
    print(data_elements)

    # 4. Calculate capacitance from step voltage and charge measurement
    CAPACITANCE = calculate_capacitance(q1=0, q2=1, v1=0, v2=10)

    # 5. Set voltage to 0 to dissipate charge from capacitor
    # 6. (Not instructed in manual but maybe?) Measure charge dissipation from capacitor
    k1.write(':ABORt')
    k1.write(':SOUR:VOLT 0')
    k1.write(':INIT')
    time.sleep(DICT_SETTINGS['sleep_before_read_buffer'])
    data2 = k1.query(":TRAC:DATA?")
    print(data2)




    # ---

    print("Script completed without errors.")