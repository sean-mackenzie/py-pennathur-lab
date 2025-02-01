import os
from os.path import join

import pandas as pd
import pyvisa
import numpy as np
import matplotlib.pyplot as plt

# --- FUNCTION FOR CONVERTING NUMPY ARRAY TO STRING LIST FOR KEITHLEY

def append_reverse(arr, single_point_max):
    """
    Append a NumPy array to itself in reverse order.
    """
    reversed_arr = arr[::-1]

    if single_point_max is True:
        reversed_arr = reversed_arr[1:]

    appended_arr = np.concatenate((arr, reversed_arr))

    return appended_arr

def numpy_array_to_string(arr, sig_figs=4):
    # Convert the NumPy array elements to strings
    # str_arr = arr.astype(str)

    # keep only significant digits
    str_arr = np.around(arr, sig_figs).astype(str)

    # Join the string elements with commas
    joined_str = ','.join(str_arr)

    return joined_str

# --- SET UP TRIGGER KEITHLEY

def setup_2410_trigger(keithley_inst, voltage_levels, delay, nplc):
    # - set up trigger keithley
    keithley_inst.write('*RST')  # Restore GPIB default
    keithley_inst.write(':FORMat:ELEMents:SENSe VOLTage, CURRent, TIME')
    keithley_inst.write(':DATA:TSTamp:FORMat DELTa')
    keithley_inst.write(':SOUR:FUNC VOLT')  # Volts source function.
    keithley_inst.write(':SOUR:VOLT:RANG 10')  # Select V-source range (n = range).
    keithley_inst.write(':SENS:FUNC "CURR:DC"')  # Current sense function.
    keithley_inst.write(':SENS:CURR:PROT %g' % 1e-3)  # 1 mA current compliance.
    keithley_inst.write(':SENS:CURR:RANG %g' % 1e-3)  # 1 mA current compliance.
    keithley_inst.write(':SENS:CURR:NPLC %g' % nplc)  # Specify integration rate (in line cycles): [0.01 to 10E3] (default = 1)

    keithley_inst.write(':SOUR:VOLT:MODE LIST')  # List volts sweep mode.
    keithley_inst.write(':SOUR:LIST:VOLT ' + numpy_array_to_string(np.array(voltage_levels)))  # List sweep points.
    keithley_inst.write(':TRIG:COUN %g' % len(voltage_levels))  # Trigger count = # sweep points.
    keithley_inst.write(':SOUR:DEL %g' % delay)  # 50ms source delay.


def setup_6517_trigger(keithley_inst, voltage_levels, nplc=0.01):
    # -
    # --- INITIALIZE KEITHLEY 6517a/b
    # -
    # RESET to defaults
    keithley_inst.write('*RST')
    # NOTE: if ZCH OFF is not explicitly sent to Keithley, then no current will be measured.
    keithley_inst.write(':SYST:ZCH OFF')  # Enable (ON) or disable (OFF) zero check (default: OFF)
    keithley_inst.write(':SYST:ZCOR ON')  # Enable (ON) or disable (OFF) zero correct (default: OFF)
    # SYSTEM
    keithley_inst.write(':SYST:RNUM:RES')  # reset reading number to zero
    keithley_inst.write(':DISP:ENAB ON')  # Enable or disable the front-panel display
    keithley_inst.write(':SYST:TSC OFF')  # Enable or disable external temperature readings (default: ON)
    keithley_inst.write(':SYST:TST:TYPE REL')  # Configure timestamp type: RELative or RTClock
    keithley_inst.write(':TRAC:FEED:CONT NEV')  # disable buffer control
    keithley_inst.write(':FORM:DATA ASCii')  # Select data format: ASCii, REAL, SREal, DREal
    keithley_inst.write(':FORM:ELEM READ,TST,VSO')  # data elements: VSOurce, READing, CHANnel, RNUMber, UNITs, TSTamp, STATus, ETEM, HUM
    # --- Define Trigger Model
    keithley_inst.write(':INIT:CONT OFF')  # When instrument returns to IDLE layer, CONTINUOUS ON = repeat; OFF = hold in IDLE
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
    keithley_inst.write(':TRIG:COUN ' + str(len(voltage_levels)))  # Set measure count (1 to 99999 or INF) (preset: INF; Reset: 1)
    keithley_inst.write(':TRIG:SOUR IMM')  # Select control source (HOLD, IMMediate, TIMer, MANual, BUS, TLINk, EXTernal) (default: IMM)
    keithley_inst.write(':TRIG:DEL 0')  # After receiving Measure Event, delay before Device Action
    # -
    # Set up Source functions
    keithley_inst.write(':SOUR:VOLT:MCON ON')  # Enable voltage source LO to ammeter LO connection (SVMI)  (default: OFF)
    keithley_inst.write(':SOUR:VOLT 4')  # Define voltage level: -1000 to +1000 V (default: 0)
    keithley_inst.write(':SOUR:VOLT:RANG 10')  # Define voltage range: <= 100: 100V, >100: 1000 V range (default: 100 V)
    keithley_inst.write(':SOUR:VOLT:LIM 5')  # Define voltage limit: 0 to 1000 V (default: 1000 V)

    # Set up Sense functions
    keithley_inst.write(':SENS:FUNC "CURR"')  # 'VOLTage[:DC]', 'CURRent[:DC]', 'RESistance', 'CHARge' (default='VOLT:DC')
    # k3.write(':SENS:CURR:APERture <n>')       # (default: 60 Hz = 16.67 ms) Set integration rate in seconds: 167e-6 to 200e-3
    keithley_inst.write(':SENS:CURR:NPLC ' + str(nplc))  # (default = 1) Set integration rate in line cycles (0.01 to 10)
    keithley_inst.write(':SENS:CURR:RANG:AUTO OFF')  # Enable (ON) or disable (OFF) autorange
    keithley_inst.write(':SENS:CURR:RANG 20e-3')  # Select current range: 0 to 20e-3 (default = 20e-3)
    keithley_inst.write(':SENS:CURR:REF 0')  # Specify reference: -20e-3 to 20e-3) (default: 0)
    keithley_inst.write(':SENS:CURR:DIG 6')  # Specify measurement resolution: 4 to 7 (default: 6)


# --- PLOTTING

def post_process_data(data_struct, idxVCTRS, source_measure_delay, NPLC, path_results, save_id, show_plot=True):
    idxV, idxC, idxT, idxR, idxSTAT = idxVCTRS
    integration_period = NPLC / 60
    # -
    samples = len(data_struct[:, idxT])
    sampling_time = data_struct[-1, idxT] - data_struct[0, idxT]
    sampling_rate = np.round(sampling_time / samples, 5)
    # -
    # --- pre-processing
    # get data
    arr_T = data_struct[:, idxT] - data_struct[0, idxT]
    arr_V = data_struct[:, idxV]
    arr_I = data_struct[:, idxC]
    # add time points to show V(t) in between current sampling times
    arr_Tt = arr_T - source_measure_delay - integration_period
    # concat
    arr_T2 = np.concatenate((arr_Tt, arr_T))
    arr_V2 = np.concatenate((arr_V, arr_V))
    # sort by time
    arr_T2, arr_V2 = list(zip(*sorted(zip(arr_T2, arr_V2))))
    # --- plotting
    # setup
    if len(arr_T) > 25:
        ms_sample = 2
        lw_time, mkr_time, ms_time = 0.5, '.', 1
    else:
        ms_sample = 5
        lw_time, mkr_time, ms_time = 1, 'o', 3
    # plot
    fig, (ax1, ax2, ax3) = plt.subplots(nrows=3, figsize=(6, 6),
                                        gridspec_kw={'height_ratios': [1, 0.65, 0.65]})

    ax1.plot(arr_T2, arr_V2, lw=lw_time, marker=mkr_time, ms=ms_time, color='gray')
    ax1.plot(arr_T, arr_V, 'o', ms=ms_sample, color='tab:blue',
             label='{}, {}'.format(np.round(sampling_time, 1), np.round(sampling_rate, 3)))
    ax1.set_xlabel('TSTamp (s)')
    ax1.set_ylabel('VOLTage (V)')
    ax1.grid(alpha=0.25)
    ax1.legend(title='sampling time and rate (s)', title_fontsize='small', fontsize='small')

    ax2.plot(arr_T, arr_I, 'o', ms=ms_sample)
    ax2.set_xlabel('TSTamp (s)')
    ax2.set_ylabel('CURRent (A)')
    ax2.grid(alpha=0.25)

    ax3.plot(arr_V, arr_I, 'o', ms=ms_sample)
    ax3.set_xlabel('VOLTage (V)')
    ax3.set_ylabel('CURRent (A)')
    ax3.grid(alpha=0.25)

    plt.suptitle(save_id)
    plt.tight_layout()
    plt.savefig(join(path_results, save_id + '.png'), dpi=300)
    if show_plot:
        plt.show()
    plt.close()


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

    k1_source_GPIB, k1_source_board_index = 25, 1  # Keithley: source measure unit
    k2_trigger_GPIB, k2_trigger_board_index, k2_inst = 24, 0, None  # '6517a'  # Keithley: used to trigger camera

    # --- INPUTS

    wid = 'W13_trace-to-C9-0pT-to-GND-to-GND'
    path_results = r'C:\Users\nanolab\Desktop\I-V\{}'.format(wid)
    if not os.path.exists(path_results):
        os.makedirs(path_results)

    test_num = 1  # 1: 150ms staircase ramp, 2,3: 500ms staircase ramp, 4: Step and Hold
    test_id = 2
    Vmax = -0.6
    Vstep = np.abs(0.02)  # always positive
    save_id = 'loc1_tid{}_test{}_{}V_{}dV'.format(test_id, test_num, Vmax, Vstep)

    # ------------------------------------------------------------------------------------------------------------------
    # SHOULD NOT NEED TO MODIFY SCRIPT BELOW
    # ------------------------------------------------------------------------------------------------------------------

    if test_num == 1:
        # Slow linear ramp
        step = Vmax / np.abs(Vmax) * Vstep
        source_measure_delay = 0.150  # (s)
        NPLC = 1
        single_point_max = True
        # VOLTAGE
        start, stop = 0, Vmax
        values = np.arange(start, stop + step / 4, step)
        values_up_and_down = append_reverse(values, single_point_max=single_point_max)
    elif test_num == 2:
        # Staircase ramp (defined step size)
        step = Vmax / np.abs(Vmax) * Vstep
        source_measure_delay = 0.5  # (s)
        NPLC = 1
        single_point_max = True
        # VOLTAGE
        start, stop = 0, Vmax
        values = np.arange(start, stop + step / 4, step)
        values_up_and_down = append_reverse(values, single_point_max=single_point_max)
    elif test_num == 3:
        # Staircase ramp (uniform steps, can be decimal values)
        step = Vmax / np.abs(Vmax) * Vstep
        source_measure_delay = 0.5  # (s)
        NPLC = 5
        single_point_max = True
        # VOLTAGE
        start, stop = 0, Vmax
        values = np.linspace(start, stop, 4)
        values_up_and_down = append_reverse(values, single_point_max=single_point_max)
    elif test_num == 4:
        # Step and Hold
        step = Vmax / np.abs(Vmax) * Vstep
        source_measure_delay = 0.35  # (s)
        NPLC = 3
        single_point_max = True
        # VOLTAGE
        start, stop = 0, Vmax
        values = np.array([0, step, Vmax, step / 5, 0])
        values_up_and_down = values  # append_reverse(values, single_point_max=single_point_max)
    else:
        raise ValueError("Test number not understood.")

    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    # --- KEITHLEY CODE

    # CURRENT
    current_range = 20E-3
    current_compliance = 20E-3
    # VOLTAGE
    values_lst = numpy_array_to_string(values_up_and_down)
    num_points = len(values_up_and_down)
    if num_points > 120:
        raise ValueError("Number of points is too large. Will cause Keithley error.")
    # FREQUENCY
    estimated_timeout = num_points * source_measure_delay * 1000 * 2 + 200  # (ms)
    # DATA TYPES
    elements_sense = 'VOLTage, CURRent, TIME'  #, RESistance, STATus
    idxVCTRS = 0, 1, 2, 3, 4
    num_elements = len(elements_sense.split(','))
    # ---
    # Trigger Keithley (these variables are only used by Keithley 2410)
    trigger_voltage = [4, 0]
    trigger_count = len(trigger_voltage)
    trigger_source_measure_delay = 0.0
    trigger_NPLC = 0.01

    # ---

    # Initialize instruments
    k1 = rm.open_resource('GPIB{}::{}::INSTR'.format(k1_source_board_index, k1_source_GPIB))
    if k2_inst is not None:
        k2 = rm.open_resource('GPIB{}::{}::INSTR'.format(k2_trigger_board_index, k2_trigger_GPIB))

    # - set up source keithley
    k1.write('*RST')  # Restore GPIB default
    k1.timeout = estimated_timeout  # Set the timeout error time (units: ms) for PyVISA
    # print("Estimated timeout: {} s".format(estimated_timeout / 1000))

    k1.write(':FORMat:ELEMents:SENSe ' + elements_sense)
    k1.write(':DATA:TSTamp:FORMat DELTa')

    # keithley.write(':SENS:FUNC:CONC OFF')  # Turn off concurrent functions.
    k1.write(':SOUR:FUNC VOLT')  # Volts source function.
    k1.write(':SOUR:VOLT:RANG MAX')  # Select V-source range (n = range).
    k1.write(':SENS:FUNC "CURR:DC"')  # Current sense function.
    k1.write(':SENS:CURR:PROT %g' % current_compliance)  # 1 mA current compliance.
    k1.write(':SENS:CURR:RANG %g' % current_range)  # 1 mA current compliance.
    k1.write(':SENS:CURR:NPLC %g' % NPLC)  # Specify integration rate (in line cycles): [0.01 to 10E3] (default = 1)

    k1.write(':SOUR:VOLT:MODE LIST')  # List volts sweep mode.
    k1.write(':SOUR:LIST:VOLT ' + values_lst)  # List sweep points.
    k1.write(':TRIG:COUN ' + str(num_points))  # Trigger count = # sweep points.
    k1.write(':SOUR:DEL %g' % source_measure_delay)  # 50ms source delay.

    # - set up trigger keithley
    if k2_inst is None:
        # --- Execute source-measure action
        k1.write(':OUTP ON')  # Turn on voltage source output
        k1.write(':INIT')  # Trigger voltage readings.
        data_stimulus = k1.query_ascii_values(':FETCh?', container=np.array)  # request data.
        data_elements = k1.query(':FORMat:ELEMents:SENSe?')
        k1.write(':OUTP OFF')
    elif k2_inst == '2410':
        setup_2410_trigger(keithley_inst=k2, voltage_levels=trigger_voltage,
                           delay=trigger_source_measure_delay, nplc=trigger_NPLC)
        """
        k2.write('*RST')  # Restore GPIB default
        k2.write(':FORMat:ELEMents:SENSe ' + elements_sense)
        k2.write(':DATA:TSTamp:FORMat DELTa')
        k2.write(':SOUR:FUNC VOLT')  # Volts source function.
        k2.write(':SOUR:VOLT:RANG 10')  # Select V-source range (n = range).
        k2.write(':SENS:FUNC "CURR:DC"')  # Current sense function.
        k2.write(':SENS:CURR:PROT %g' % 1e-3)  # 1 mA current compliance.
        k2.write(':SENS:CURR:RANG %g' % 1e-3)  # 1 mA current compliance.
        k2.write(':SENS:CURR:NPLC %g' % trigger_NPLC)  # Specify integration rate (in line cycles): [0.01 to 10E3] (default = 1)
    
        k2.write(':SOUR:VOLT:MODE LIST')  # List volts sweep mode.
        k2.write(':SOUR:LIST:VOLT ' + numpy_array_to_string(np.array(trigger_voltage)))  # List sweep points.
        k2.write(':TRIG:COUN %g' % trigger_count)  # Trigger count = # sweep points.
        k2.write(':SOUR:DEL %g' % trigger_source_measure_delay)  # 50ms source delay.
        """

        # --- Execute source-measure action

        # Initialize both Keithleys (but don't set a voltage level)
        k2.write(':OUTP ON')  # Turn on camera trigger output.
        k1.write(':OUTP ON')  # Turn on voltage source output.

        # Trigger a very fast reading from trigger Keithley, then trigger source Keithley
        k2.write(':INIT')  # Trigger camera readings.
        k1.write(':INIT')  # Trigger voltage readings.

        data_stimulus = k1.query_ascii_values(':FETCh?', container=np.array)  # request data.
        data_delay = k2.query_ascii_values(':FETCh?', container=np.array)  # request data.
        data_elements = k1.query(':FORMat:ELEMents:SENSe?')

        # close instruments
        k1.write(':OUTP OFF')
        k2.write(':OUTP OFF')
    elif k2_inst == '6517a':
        # NOTE: the variable voltage_levels and nplc have no effect on Keithley 6517 triggering.
        # All "synchronization" settings are pre-programmed to be as fast as possible
        # and no data is recorded.
        setup_6517_trigger(keithley_inst=k2, voltage_levels=trigger_voltage, nplc=trigger_NPLC)
        """
        # Execute configured measurement
        k3.write('OUTP ON')  # Turn source ON
        k3.write(':SYST:TST:REL:RES')  # Reset relative timestamp to zero seconds
        k3.write(':INIT')  # Move from IDLE state to ARM Layer 1
        """

        # --- Execute source-measure action

        # initialize the source Keithley
        k1.write(':OUTP ON')  # Turn on voltage source output (but no voltage level will be set until triggered)

        # For Keithley 6517a, the following command will source a non-zero voltage, and thus trigger the camera
        k2.write(':OUTP ON')  # Turn on trigger voltage source to whatever voltage level was set.

        # Trigger the source Keithley
        k1.write(':INIT')  # Trigger voltage readings.
        data_stimulus = k1.query_ascii_values(':FETCh?', container=np.array)  # request data.
        data_elements = k1.query(':FORMat:ELEMents:SENSe?')
        # close instruments
        k1.write(':OUTP OFF')
        k2.write(':SOUR:VOLT 0')
        k2.write(':OUTP OFF')
    else:
        raise ValueError("Trigger instrument not understood.")

    # --- Execute source-measure action

    """
    # k2.write(':OUTP ON')  # Turn on camera trigger output.
    k1.write(':OUTP ON')  # Turn on voltage source output.

    # k2.write(':INIT')  # Trigger camera readings.
    k2.write(':OUTP ON')  # Turn on camera trigger output.
    k1.write(':INIT')  # Trigger voltage readings.

    data_stimulus = k1.query_ascii_values(':FETCh?', container=np.array)  # request data.
    # data_delay = k2.query_ascii_values(':FETCh?', container=np.array)  # request data.

    # close instruments
    data_elements = k1.query(':FORMat:ELEMents:SENSe?')
    k1.write(':OUTP OFF')
    k2.write(':SOUR:VOLT 0')
    k2.write(':OUTP OFF')
    """

    # ---

    # post-process stimulus data
    data_struct = np.reshape(data_stimulus, (num_points, num_elements))
    pd.DataFrame(data_struct, columns=data_elements.split(',')).to_excel(join(path_results, save_id + '.xlsx'))
    post_process_data(data_struct, idxVCTRS,
                      source_measure_delay, NPLC,
                      path_results, save_id,
                      show_plot=True)
    # ---
    # post-process trigger data
    if k2_inst == '2410':
        data_struct2 = np.reshape(data_delay, (trigger_count, num_elements))
        pd.DataFrame(data_struct2, columns=data_elements.split(',')).to_excel(join(path_results, save_id + '_trigger.xlsx'))





