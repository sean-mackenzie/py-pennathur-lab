import os
from os.path import join
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pyvisa
import time


def setup_6517_amplifier_monitor(keithley_inst, settings):
    """
    Hardware configuration for unguarded voltage measurement:
        1. The HI (red) from triax cable should be connected for high voltage side (i.e., amplifier output).
        2. The LO (black) from triax cable should be connected for low voltage side (i.e., ground).
    :param keithley_inst:
    :param nplc:
    :return:
    """
    # -
    k1_integration_period = k1_nplc / 60
    k1_delay_time = k1_integration_period * 2
    estimated_timeout = k1_num_samples * k1_integration_period * 1000  # (ms)
    print("estimate timeout: {} seconds".format(estimated_timeout / 1000))
    k1.timeout = estimated_timeout  # Set the timeout error time (units: ms) for PyVISA
    if k1_monitor == 'CURR':
        k1_measure_units = '1V/40mA'
    elif k1_monitor == 'VOLT':
        k1_measure_units = '1V/100V'
    else:
        raise ValueError("Invalid monitor type.")
    # -
    # --- INITIALIZE KEITHLEY 6517a/b
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
    keithley_inst.write(':TRIG:COUN ' + str(num_samples))  # Set measure count (1 to 99999 or INF)
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
    keithley_inst.write(':SENS:VOLT:NPLC ' + str(nplc))  # (default = 1) Set integration rate in line cycles (0.01 to 10)
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


def setup_agilent_awg(agilent_inst, settings):
    dict_settings = {
        'save_id': save_id,
        'awg_wave': awg_wave,
        'awg_freq': awg_freq,
        'awg_square_duty_cycle': awg_square_duty_cycle,
        'awg_volt_unit': awg_volt_unit,
        'Vapp': Vapp,
        'Voffset': Voffset,
        'trek_ampli': trek_ampli,
        # 'awg_volt': awg_volt,
        # 'awg_volt_offset': awg_volt_offset,
        'awg_output_termination': awg_output_termination,
        'k1_monitor': k1_monitor,
        'k1_nplc': k1_nplc,
        'k1_num_samples': k1_num_samples,
        # 'k1_integration_period': k1_integration_period,
        # 'k1_delay_time': k1_delay_time,
        # 'k1_measure_units': k1_measure_units,
        # 'estimated_timeout': estimated_timeout,
    }

    awg_volt, awg_volt_offset = np.round(Vapp / trek_ampli, 3), np.round(Voffset / trek_ampli, 2)
    # -
    if awg_volt + awg_volt_offset > 18:
        raise ValueError("AWG max Vpp + Voffset is 20.")
    elif awg_volt > 18:
        raise ValueError("AWG max Vpp is 20.")
    else:
        print("AWG Voltage Output: {} {} + {} DC".format(awg_volt, awg_volt_unit, awg_volt_offset))
        print("TREK Voltage Output: {} {} + {} DC".format(Vapp, awg_volt_unit, Voffset))

    awg.write('*RST')  # Restore GPIB default
    # Program physical/hardware set up
    awg.write('OUTP:LOAD ' + str(awg_output_termination))  # OUTPut:LOAD {<ohms>|INFinity|MINimum|MAXimum}
    # NOTE 1: the input impedance of the Trek Amplifier is 90 kOhms.
    # NOTE 2: it seems the "most appropriate" output termination for Trek is 10 kOhms.

    # Program waveform
    awg.write('FUNC ' + awg_wave)  # FUNCtion {SINusoid|SQUare|RAMP|PULSe|NOISe|DC|USER}
    awg.write('FREQ ' + str(awg_freq))  # FREQuency {<frequency>|MINimum|MAXimum}
    awg.write('VOLT ' + str(awg_volt))  # VOLTage {<amplitude>|MINimum|MAXimum}
    awg.write('VOLT:OFFS ' + str(awg_volt_offset))  # VOLTage:OFFSet {<offset>|MINimum|MAXimum}
    awg.write('VOLT:UNIT ' + awg_volt_unit)  # VOLTage:UNIT {VPP|VRMS|DBM}
    awg.write('VOLT:RANG:AUTO ON')  # VOLTage:RANGe:AUTO {OFF|ON|ONCE}
    if awg_wave == 'SQU':
        awg.write('FUNC:SQU:DCYC ' + str(awg_square_duty_cycle))  # FUNCtion:SQUare:DCYCle {<percent>|MINimum|MAXimum}

# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":

    # --- SETUP
    rm = pyvisa.ResourceManager()
    check_inst = False  # True False
    if check_inst is True:
        print(rm.list_resources())  # only list "::INSTR" resources
        # # returns something like: ('ASRL1::INSTR', 'ASRL2::INSTR', 'GPIB0::14::INSTR')
        raise ValueError("Check instruments are connected.")

    # --- PROGRAMMING
    # AWG_GPIB, AWG_BOARD_INDEX = 10, 0  # Arbitrary waveform generator (awg)
    AWG_USB = 'USB0::0x0957::0x1507::MY48003320::INSTR'  # None
    K1_GPIB, K1_BOARD_INDEX = 24, 0  # Arbitrary waveform generator (awg)
    AMPLIFIER_GAIN = 50
    AWG_OUTPUT_TERMINATION = '10E3'

    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    # Setup
    SAVE_DIR = r'C:\Users\nanolab\Desktop\sean\Agilent-Keithley-Andor Synchronization\Test-Current-Monitor'

    TID = 6
    # -
    # Agilent 33210A arbitrary waveform generator
    AWG_WAVE = 'SIN'  # SIN, SQU, RAMP, PULS, DC
    AWG_FREQ = 0.25  # 0.001 to 10000000
    AWG_SQUARE_DUTY_CYCLE = 50  # 20 to 80 (square waves only)
    AWG_VOLT_UNIT = 'VPP'  # VPP, VRMS
    TARGET_VOLT, VOFFSET = 200, 0
    # -
    # Keithley 6517a monitor
    k1_monitor = 'CURR'  # 'CURR' or 'VOLT
    k1_nplc, k1_num_samples = 1, 250
    # -
    # save id
    save_id = ('tid{}_{}_{}Hz_{}pDC_{}{}_{}VDCoffset'.format(tid, awg_wave, awg_freq,
                                                             awg_square_duty_cycle,
                                                             Vapp, awg_volt_unit, Voffset))

    if tid is not None:
        dict_settings = {
            'save_id': save_id,
            'awg_wave': awg_wave,
            'awg_freq': awg_freq,
            'awg_square_duty_cycle': awg_square_duty_cycle,
            'awg_volt_unit': awg_volt_unit,
            'Vapp': Vapp,
            'Voffset': Voffset,
            'trek_ampli': trek_ampli,
            #'awg_volt': awg_volt,
            #'awg_volt_offset': awg_volt_offset,
            'awg_output_termination': awg_output_termination,
            'k1_monitor': k1_monitor,
            'k1_nplc': k1_nplc,
            'k1_num_samples': k1_num_samples,
            #'k1_integration_period': k1_integration_period,
            #'k1_delay_time': k1_delay_time,
            #'k1_measure_units': k1_measure_units,
            #'estimated_timeout': estimated_timeout,
        }

    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    # --- Initialize instruments
    # Agilent 33210A arbitrary waveform generator
    awg = rm.open_resource(awg_usb)  # 'GPIB{}::{}::INSTR'.format(awg_board_index, awg_GPIB)
    # Keithley 6517a electrometer
    k1 = rm.open_resource('GPIB{}::{}::INSTR'.format(k1_board_index, k1_GPIB))

    # -

    # --- Program instruments
    dict_settings = setup_agilent_awg(agilent_inst=awg, settings=dict_settings)
    dict_settings = setup_6517_amplifier_monitor(keithley_inst=k1, settings=dict_settings)

    # -----------------



    awg.write('OUTP ON')  # OUTPut {OFF|ON}


    # Trigger the monitor Keithley
    k1.write(':SYST:TST:REL:RES')  # Reset relative timestamp to 0.
    k1.write(':INIT')  # Trigger voltage readings.
    data_monitor = []
    for i in range(k1_num_samples):
        time.sleep(k1_delay_time)
        datum = k1.query_ascii_values(':FETCh?', container=np.array)  # request data.
        data_monitor.append(datum)
        # print("{}: {}".format(i, datum))

    time.sleep(1)

    awg.write('OUTP OFF')

    # post-process stimulus data
    # -
    # --- parse, package, and export
    data_elements = k1.query(':FORMat:ELEM?').rstrip()
    print(data_elements)
    # df = parse_ascii(d=data, e=data_elements, as_type='pd.DataFrame')
    data_monitor = np.array(data_monitor)
    df = pd.DataFrame(data_monitor, columns=data_elements.split(','))
    df_settings = pd.DataFrame.from_dict(data=dict_settings, orient='index')

    file = join(save_dir, '{}_data.xlsx'.format(save_id))
    sns, dfs = ['data', 'settings'], [df, df_settings]
    idx, lbls = [False, True], [None, 'k']
    with pd.ExcelWriter(file) as writer:
        for sheet_name, dataframe, idx, idx_lbl in zip(sns, dfs, idx, lbls):
            dataframe.to_excel(writer, sheet_name=sheet_name, index=idx, index_label=idx_lbl)

    # --- PLOTTING

    # setup
    # df.columns = ['READ', 'TST']
    print(df.columns)
    py, px = df.columns

    dt = df[px].iloc[-1]
    num_samples = len(df)
    samples_per_second = np.round(num_samples / dt, 2)
    print("{} samples / {} s = {} samples/s".format(num_samples, dt, samples_per_second))

    fig, ax1 = plt.subplots()#nrows=3, figsize=(10, 10))

    ax1.plot(df[px], df[py], '-o', ms=2, label=samples_per_second)
    ax1.set_xlabel('{} (s)'.format(px))
    ax1.set_ylabel(k1_measure_units)
    ax1.grid(alpha=0.2)
    ax1.legend(title='#/s', loc='upper right', fontsize='small')

    plt.suptitle(save_id)
    plt.tight_layout()
    plt.savefig(join(save_dir, 'fig_{}.png'.format(save_id)), dpi=300, facecolor='w', bbox_inches='tight')
    plt.show()
    plt.close()

    print("Completed without errors.")