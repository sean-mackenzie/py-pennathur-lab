import os
from os.path import join
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pyvisa
import time


def package_data_and_export(data, data_elements, settings, return_df):
    df = pd.DataFrame(data, columns=data_elements.split(','))
    df_settings = pd.DataFrame.from_dict(data=settings, orient='index')

    file = join(settings['save_dir'], '{}_data.xlsx'.format(settings['save_id']))
    sns, dfs = ['data', 'settings'], [df, df_settings]
    idx, lbls = [False, True], [None, 'k']
    with pd.ExcelWriter(file) as writer:
        for sheet_name, dataframe, idx, idx_lbl in zip(sns, dfs, idx, lbls):
            dataframe.to_excel(writer, sheet_name=sheet_name, index=idx, index_label=idx_lbl)
    if return_df:
        return df

def plot_arbitrary_waveform_monitor_and_monitor(df, settings):
    # setup
    # df.columns = ['READ', 'TST']
    py, px = df.columns

    # sampling rate
    dt = df[px].iloc[-1]
    num_samples = len(df)
    samples_per_second = np.round(num_samples / dt, 2)

    # plot
    fig, ax1 = plt.subplots()#nrows=3, figsize=(10, 10))
    ax1.plot(df[px], df[py], '-o', ms=2, label=samples_per_second)
    ax1.set_xlabel('{} (s)'.format(px))
    ax1.set_ylabel(settings['keithley_measure_units'])
    ax1.grid(alpha=0.2)
    ax1.legend(title='#/s', loc='upper right', fontsize='small')
    plt.suptitle(settings['save_id'])
    plt.tight_layout()
    plt.savefig(join(settings['save_dir'], 'fig_{}.png'.format(settings['save_id'])),
                dpi=300, facecolor='w', bbox_inches='tight')
    plt.show()
    plt.close()

def post_process_data(data, data_elements, settings):
    df = package_data_and_export(data, data_elements, settings, return_df=True)
    plot_arbitrary_waveform_monitor_and_monitor(df=df, settings=settings)



def setup_keithley_6517_amplifier_monitor(keithley_inst, settings):
    """
    Hardware configuration for unguarded voltage measurement:
        1. The HI (red) from triax cable should be connected for high voltage side (i.e., amplifier output).
        2. The LO (black) from triax cable should be connected for low voltage side (i.e., ground).
    :param keithley_inst:
    :param settings:
    :return:
    """
    # hard-coded Keithley modifiers
    ratio_fetch_to_integration = 2
    # -
    integration_period = settings['keithley_nplc'] / 60
    fetch_delay = integration_period * ratio_fetch_to_integration
    estimated_timeout = settings['keithley_num_samples'] * integration_period  # (seconds)
    print("estimated timeout: {} seconds".format(estimated_timeout))
    if settings['keithley_monitor'] == 'CURR':
        measure_units = '1V/40mA'
    elif settings['keithley_monitor'] == 'VOLT':
        measure_units = '1V/100V'
    else:
        raise ValueError("Invalid monitor type.")
    keithley_settings = {
        'keithley_measure_units': measure_units,
        'keithley_integration_period': integration_period,
        'keithley_fetch_delay': fetch_delay,
        'keithley_ratio_fetch_to_integration': ratio_fetch_to_integration,
        'keithley_timeout': estimated_timeout,
    }
    settings.update(keithley_settings)
    # -
    # --- INITIALIZE KEITHLEY 6517a/b
    # -
    # Set instrument timeout
    keithley_inst.timeout = estimated_timeout * 1000  # Set the timeout error time (units: ms) for PyVISA
    # -
    # 1. RESET to defaults
    keithley_inst.write('*RST')
    # 2. SYSTEM
    keithley_inst.write(':SYST:RNUM:RES')  # reset reading number to zero
    keithley_inst.write(':SYST:TSC OFF')  # Enable or disable external temperature readings (default: ON)
    keithley_inst.write(':SYST:TST:TYPE REL')  # Configure timestamp type: RELative or RTClock
    keithley_inst.write(':TRAC:FEED:CONT NEV')  # disable buffer control
    keithley_inst.write(':FORM:DATA ASCii')  # Select data format: ASCii, REAL, SREal, DREal
    keithley_inst.write(':FORM:ELEM READ,TST')  # data elements: VSOurce, READing, CHANnel, RNUMber, UNITs, TSTamp, STATus, ETEM, HUM

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
    keithley_inst.write(':TRIG:TCON:DIR ACC')  # Wait for trigger event (TLINK)
    keithley_inst.write(':TRIG:COUN ' + str(settings['keithley_num_samples']))  # Set measure count (1 to 99999 or INF)
    keithley_inst.write(':TRIG:SOUR IMM')  # Select control source (HOLD, IMMediate, TIMer, MANual, BUS, TLINk, EXTernal) (default: IMM)
    keithley_inst.write(':TRIG:DEL 0')  # After receiving Measure Event, delay before Device Action

    # 3. Always enable zero check when setting up instrument functions
    keithley_inst.write(':SYST:ZCH ON')  # Enable (ON) or disable (OFF) zero check (default: OFF)

    # 4. Set up Sense functions
    keithley_inst.write(':DISP:ENAB OFF')  # Enable or disable the front-panel display
    # Sense functions
    keithley_inst.write(':SENS:FUNC "VOLT"')  # 'VOLTage[:DC]', 'CURRent[:DC]', 'RESistance', 'CHARge' (default='VOLT:DC')
    keithley_inst.write(':SENS:VOLT:DC:GUARd OFF')  # Disable guard
    # k3.write(':SENS:CURR:APERture <n>')       # (default: 60 Hz = 16.67 ms) Set integration rate in seconds: 167e-6 to 200e-3
    keithley_inst.write(':SENS:VOLT:NPLC ' + str(settings['keithley_nplc']))  # (default = 1) Set integration rate in line cycles (0.01 to 10)
    # --- perform zero correct
    # see page 248 of manual for instructions
    # --- end zero correct
    # now, set measurement range
    keithley_inst.write(':SENS:VOLT:RANG:AUTO OFF')  # Enable (ON) or disable (OFF) autorange
    keithley_inst.write(':SENS:VOLT:RANG 10')  # Select current range: 0 to 20e-3 (default = 20e-3)
    keithley_inst.write(':SENS:VOLT:REF 0')  # Specify reference: -20e-3 to 20e-3) (default: 0)
    keithley_inst.write(':SENS:VOLT:DIG 6')  # Specify measurement resolution: 4 to 7 (default: 6)

    # disable zero check immediately before measurement
    keithley_inst.write(':SYST:ZCOR OFF')  # Enable (ON) or disable (OFF) zero correct (default: OFF)
    keithley_inst.write(':SYST:ZCH OFF')  # Enable (ON) or disable (OFF) zero check (default: OFF)

    return settings

def required_input_to_amplifier(gain, output_voltage, dc_offset):
    req_input_volt = np.round(output_voltage / gain, 3)
    req_input_dc_offset = np.round(dc_offset / gain, 3)
    return req_input_volt, req_input_dc_offset

def setup_agilent_awg(agilent_inst, settings):
    # -
    if settings['awg_volt'] + settings['awg_dc_offset'] > 18:
        raise ValueError("AWG max Vpp + Voffset is 20.")
    elif settings['awg_volt'] > 18:
        raise ValueError("AWG max Vpp is 20.")
    else:
        print("AWG Voltage Output: {} {} + {} DC".format(settings['awg_volt'], settings['awg_volt_unit'], settings['awg_dc_offset']))
        print("TREK Voltage Output: {} {} + {} DC".format(settings['output_volt'], settings['awg_volt_unit'], settings['output_dc_offset']))

    awg.write('*RST')  # Restore GPIB default
    # Program physical/hardware set up
    awg.write('OUTP:LOAD ' + str(settings['awg_output_termination']))  # OUTPut:LOAD {<ohms>|INFinity|MINimum|MAXimum}
    # NOTE 1: the input impedance of the Trek Amplifier is 90 kOhms.
    # NOTE 2: it seems the "most appropriate" output termination for Trek is 10 kOhms.

    # Program waveform
    awg.write('FUNC ' + settings['awg_wave'])  # FUNCtion {SINusoid|SQUare|RAMP|PULSe|NOISe|DC|USER}
    awg.write('FREQ ' + str(settings['awg_freq']))  # FREQuency {<frequency>|MINimum|MAXimum}
    awg.write('VOLT ' + str(settings['awg_volt']))  # VOLTage {<amplitude>|MINimum|MAXimum}
    awg.write('VOLT:OFFS ' + str(settings['awg_dc_offset']))  # VOLTage:OFFSet {<offset>|MINimum|MAXimum}
    awg.write('VOLT:UNIT ' + settings['awg_volt_unit'])  # VOLTage:UNIT {VPP|VRMS|DBM}
    awg.write('VOLT:RANG:AUTO ON')  # VOLTage:RANGe:AUTO {OFF|ON|ONCE}
    if awg_wave == 'SQU':
        awg.write('FUNC:SQU:DCYC ' + str(settings['awg_square_duty_cycle']))  # FUNCtion:SQUare:DCYCle {<percent>|MINimum|MAXimum}


def data_acquisition_handler(agilent_inst, keithley_inst, settings):
    # 1. Trigger the Keithley to start recording data
    keithley_inst.write(':SYST:TST:REL:RES')  # Reset relative timestamp to 0.
    keithley_inst.write(':INIT')  # Trigger voltage readings.

    # 2. Start sourcing voltage from arbitrary waveform
    agilent_inst.write('OUTP ON')  # OUTPut {OFF|ON}

    # 3. Handle periodic data acquisition
    data = []
    for i in range(settings['keithley_num_samples']):
        time.sleep(settings['keithley_fetch_delay'])
        datum = k1.query_ascii_values(':FETCh?', container=np.array)  # request data.
        data.append(datum)

    # 4. Stop sourcing voltage
    awg.write('OUTP OFF')

    # 5. Return data and elements
    data = np.array(data)
    data_elements = keithley_inst.query(':FORMat:ELEM?').rstrip()

    return data, data_elements

# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":

    # --- HARDWARE SETUP
    # available instruments
    rm = pyvisa.ResourceManager()
    check_inst = False  # True False
    if check_inst is True:
        print(rm.list_resources())  # only list "::INSTR" resources
        raise ValueError("Check instruments are connected.")
    # instrument addresses
    # Agilent 33210A aribtrary waveform generator
    AWG_USB = 'USB0::0x0957::0x1507::MY48003320::INSTR'  # or, AWG_GPIB, AWG_BOARD_INDEX = 10, 0
    AMPLIFIER_GAIN = 50
    AWG_OUTPUT_TERMINATION = '10E3'
    # Keithley 6517 electrometer
    K1_GPIB, K1_BOARD_INDEX = 24, 0

    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    # --- TEST SETUP

    # root directory
    BASE_DIR = r'C:\Users\nanolab\Desktop\sean\Agilent-Keithley-Andor Synchronization'

    # test id
    TEST_SUBJECT = 'Test-Current-Monitor'
    TID = 6

    # Agilent 33210A arbitrary waveform generator
    AWG_WAVE = 'SIN'  # SIN, SQU, RAMP, PULS, DC
    AWG_FREQ = 0.25  # 0.001 to 10000000
    OUTPUT_VOLT = 200  # max bipolar: 350 V; max unipolar: 700 V
    OUTPUT_DC_OFFSET = 0  # max: 350 V
    AWG_SQUARE_DUTY_CYCLE = 50  # 20 to 80 (square waves only)
    AWG_VOLT_UNIT = 'VPP'  # VPP, VRMS

    # Keithley 6517a monitor
    K1_MONITOR = 'CURR'  # 'CURR' or 'VOLT
    K1_NPLC = 1  # 0.01 to 10
    K1_NUM_SAMPLES = 250

    # ---

    # setup directories and filenames for export
    SAVE_ID = ('tid{}_{}_{}Hz_{}pDC_{}{}_{}VDC-offset'.format(
        TID, AWG_WAVE, AWG_FREQ, AWG_SQUARE_DUTY_CYCLE, OUTPUT_VOLT, AWG_VOLT_UNIT, OUTPUT_DC_OFFSET))
    SAVE_DIR = join(BASE_DIR, TEST_SUBJECT)
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    if TID is not None:
        AWG_VOLT, AWG_DC_OFFSET = required_input_to_amplifier(
            gain=AMPLIFIER_GAIN,
            output_voltage=OUTPUT_VOLT,
            dc_offset=OUTPUT_DC_OFFSET,
        )
        DICT_SETTINGS = {
            'tid': TID,
            'save_dir': SAVE_DIR,
            'save_id': SAVE_ID,
            'output_volt': OUTPUT_VOLT,
            'output_dc_offset': OUTPUT_DC_OFFSET,
            'awg_wave': AWG_WAVE,
            'awg_freq': AWG_FREQ,
            'awg_square_duty_cycle': AWG_SQUARE_DUTY_CYCLE,
            'awg_volt_unit': AWG_VOLT_UNIT,
            'awg_volt': AWG_VOLT,
            'awg_dc_offset': AWG_DC_OFFSET,
            'awg_output_termination': AWG_OUTPUT_TERMINATION,
            'amplifier_gain': AMPLIFIER_GAIN,
            'keithley_monitor': K1_MONITOR,
            'keithley_nplc': K1_NPLC,
            'keithley_num_samples': K1_NUM_SAMPLES,
        }
    else:
        raise ValueError("Must define tid.")

    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    # --- Initialize instruments
    AWG = rm.open_resource(AWG_USB)  # 'GPIB{}::{}::INSTR'.format(awg_board_index, awg_GPIB)
    K1 = rm.open_resource('GPIB{}::{}::INSTR'.format(K1_BOARD_INDEX, k1_GPIB))
    # -
    # --- Program instruments
    DICT_SETTINGS = setup_agilent_awg(agilent_inst=AWG, settings=DICT_SETTINGS)
    DICT_SETTINGS = setup_keithley_6517_amplifier_monitor(keithley_inst=K1, settings=DICT_SETTINGS)
    # -
    # --- Acquire data
    DATA, DATA_ELEMENTS = data_acquisition_handler(
        agilent_inst=AWG,
        keithley_inst=K1,
        settings=DICT_SETTINGS,
    )
    # -
    # - Post-process data and save
    post_process_data(
        data=DATA,
        data_elements=DATA_ELEMENTS,
        settings=DICT_SETTINGS,
    )



    print("Completed without errors.")