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

def numpy_array_to_string(arr):
    # Convert the NumPy array elements to strings
    str_arr = arr.astype(str)

    # Join the string elements with commas
    joined_str = ','.join(str_arr)

    return joined_str


def post_process_data(data_struct, idxVCTRS, NPLC, path_results, save_id, show_plot=True):
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
    arr_Tt = arr_T[1:] - integration_period
    arr_Vt = arr_V[:-1]
    # concat
    arr_T2 = np.concatenate((arr_T, arr_Tt))
    arr_V2 = np.concatenate((arr_V, arr_Vt))
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
    # print(rm.list_resources())  # only list "::INSTR" resources
    # # returns something like: ('ASRL1::INSTR', 'ASRL2::INSTR', 'GPIB0::14::INSTR')

    k1_source_GPIB, k1_source_board_index = 25, 0  # Keithley: source measure unit
    k2_trigger_GPIB, k2_trigger_board_index = 23, 1  # Keithley: used to trigger camera

    # --- INPUTS

    path_results = r'C:\Users\nanolab\Desktop\test\I-V'
    test_id = 1
    test_num = 1  # 1: Slow linear ramp, 2,3: Staircase ramp defined/arbitrary steps, 4: Step and Hold
    Vmax = 250
    Vstep = np.abs(5)  # always positive
    save_id = 'tid{}_test{}_{}V_{}dV'.format(test_id, test_num, Vmax, Vstep)


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
    current_range = 1E-6
    # VOLTAGE
    values_lst = numpy_array_to_string(values_up_and_down)
    num_points = len(values_up_and_down)
    # FREQUENCY
    estimated_timeout = num_points * source_measure_delay * 1000 * 2 + 200  # (ms)
    # DATA TYPES
    elements_sense = 'VOLTage, CURRent, TIME'  #, RESistance, STATus
    idxVCTRS = 0, 1, 2, 3, 4
    num_elements = len(elements_sense.split(','))

    # ---

    # Initialize instruments
    k1 = rm.open_resource('GPIB{}::{}::INSTR'.format(k1_source_board_index, k1_source_GPIB))
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
    k1.write(':SENS:CURR:PROT %g' % current_range)  # 1 mA current compliance.
    k1.write(':SENS:CURR:RANG %g' % current_range)  # 1 mA current compliance.
    k1.write(':SENS:CURR:NPLC %g' % NPLC)  # Specify integration rate (in line cycles): [0.01 to 10E3] (default = 1)

    k1.write(':SOUR:VOLT:MODE LIST')  # List volts sweep mode.
    k1.write(':SOUR:LIST:VOLT ' + values_lst)  # List sweep points.
    k1.write(':TRIG:COUN ' + str(num_points))  # Trigger count = # sweep points.
    k1.write(':SOUR:DEL %g' % source_measure_delay)  # 50ms source delay.

    # - set up trigger keithley
    k2.write('*RST')  # Restore GPIB default
    k2.write(':FORMat:ELEMents:SENSe ' + elements_sense)
    k2.write(':DATA:TSTamp:FORMat DELTa')
    k2.write(':SOUR:FUNC VOLT')  # Volts source function.
    k2.write(':SOUR:VOLT:RANG 10')  # Select V-source range (n = range).
    k2.write(':SENS:FUNC "CURR:DC"')  # Current sense function.
    k2.write(':SENS:CURR:PROT %g' % 1e-3)  # 1 mA current compliance.
    k2.write(':SENS:CURR:RANG %g' % 1e-3)  # 1 mA current compliance.
    k2.write(':SENS:CURR:NPLC %g' % 1)  # Specify integration rate (in line cycles): [0.01 to 10E3] (default = 1)

    k2.write(':SOUR:VOLT:MODE LIST')  # List volts sweep mode.
    k2.write(':SOUR:LIST:VOLT 4,4,0')  # List sweep points.
    k2.write(':TRIG:COUN 5')  # Trigger count = # sweep points.
    k2.write(':SOUR:DEL %g' % 0.05)  # 50ms source delay.

    # --- Execute source-measure action

    k2.write(':OUTP ON')  # Turn on camera trigger output.
    k1.write(':OUTP ON')  # Turn on voltage source output.

    k2.write(':INIT')  # Trigger camera readings.
    k1.write(':INIT')  # Trigger voltage readings.

    # data = k2.query_ascii_values(':READ?', container=np.array)  # send trigger to camera
    data = k1.query_ascii_values(':FETCh?', container=np.array)  # trigger voltage sweep, request data.

    # ---

    # close instruments
    data_elements = k1.query(':FORMat:ELEMents:SENSe?')
    k1.write(':OUTP OFF')
    k2.write(':OUTP OFF')

    # post-process data
    data_struct = np.reshape(data, (num_points, num_elements))
    # save data
    pd.DataFrame(data_struct, columns=data_elements.split(',')).to_excel(join(path_results, save_id + '.xlsx'))
    # plot and save plot
    post_process_data(data_struct, idxVCTRS, NPLC, path_results, save_id, show_plot=True)





