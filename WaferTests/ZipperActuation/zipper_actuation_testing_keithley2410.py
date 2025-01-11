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


# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":

    # --- INPUTS

    path_results = r'C:\Users\nanolab\Desktop\sean'
    test_num = 2  # 1: Observe by-eye, 2: Slow linear ramp, 3: Fast ramp, 4: Staircase ramp, 5: Step and Hold
    Vmax, Vstep = 5, 0.5
    save_id = 'test1_test{}_{}V'.format(test_num, Vmax)
    save_fig = True

    GPIB = 25


    # ------------------------------------------------------------------------------------------------------------------
    # SHOULD NOT NEED TO MODIFY SCRIPT BELOW
    # ------------------------------------------------------------------------------------------------------------------

    if test_num == 1:
        # Observe by-eye: linear ramp at speed that can be observed by eye.
        step = Vmax / np.abs(Vmax) * Vstep
        source_measure_delay = 0.15  # (s)
        NPLC = 2  # (Number of Power Line Cycles) integration rate (in line cycles): [0.01 to 10E3] (default = 1)
        single_point_max = False
        # VOLTAGE
        start, stop = 0, Vmax
        values = np.arange(start, stop + step / 4, step)
        values_up_and_down = append_reverse(values, single_point_max=single_point_max)
    elif test_num == 2:
        # Slow linear ramp
        step = Vmax / np.abs(Vmax) * Vstep
        source_measure_delay = 0.05  # (s)
        NPLC = 1
        single_point_max = True
        # VOLTAGE
        start, stop = 0, Vmax
        values = np.arange(start, stop + step / 4, step)
        values_up_and_down = append_reverse(values, single_point_max=single_point_max)
    elif test_num == 3:
        # Fast linear ramp
        step = Vmax / np.abs(Vmax) * Vstep
        source_measure_delay = 0.025  # (s)
        NPLC = 0.1
        single_point_max = True
        # VOLTAGE
        start, stop = 0, Vmax
        values = np.arange(start, stop + step / 4, step)
        values_up_and_down = append_reverse(values, single_point_max=single_point_max)
    elif test_num == 4:
        # Staircase ramp
        step = Vmax / np.abs(Vmax) * Vstep
        source_measure_delay = 0.5  # (s)
        NPLC = 5
        single_point_max = True
        # VOLTAGE
        start, stop = 0, Vmax
        values = np.linspace(start, stop, 4)
        values_up_and_down = append_reverse(values, single_point_max=single_point_max)
    elif test_num == 5:
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
    integration_period = NPLC / 60
    estimated_timeout = num_points * source_measure_delay * 1000 * 2 + 0.2  # (ms)

    # DATA TYPES
    elements_sense = 'VOLTage, CURRent, TIME'  #, RESistance, STATus
    idxV, idxC, idxT, idxR, idxSTAT = 0, 1, 2, 3, 4
    num_elements = len(elements_sense.split(','))

    # ---

    rm = pyvisa.ResourceManager()
    keithley = rm.open_resource("GPIB::{}".format(GPIB))

    # 0.
    keithley.write('*RST')  # Restore GPIB default
    keithley.timeout = estimated_timeout  # Set the timeout error time (units: ms) for PyVISA
    print("Estimated timeout: {} s".format(estimated_timeout / 1000))

    keithley.write(':FORMat:ELEMents:SENSe ' + elements_sense)
    keithley.write(':DATA:TSTamp:FORMat DELTa')

    # keithley.write(':SENS:FUNC:CONC OFF')  # Turn off concurrent functions.
    keithley.write(':SOUR:FUNC VOLT')  # Volts source function.
    keithley.write(':SOUR:VOLT:RANG MAX')  # Select V-source range (n = range).
    keithley.write(':SENS:FUNC "CURR:DC"')  # Current sense function.
    keithley.write(':SENS:CURR:PROT %g' % current_range)  # 1 mA current compliance.
    keithley.write(':SENS:CURR:RANG %g' % current_range)  # 1 mA current compliance.
    keithley.write(':SENS:CURR:NPLC %g' % NPLC)  # Specify integration rate (in line cycles): [0.01 to 10E3] (default = 1)


    keithley.write(':SOUR:VOLT:MODE LIST')  # List volts sweep mode.
    keithley.write(':SOUR:LIST:VOLT ' + values_lst)  # List sweep points.
    keithley.write(':TRIG:COUN ' + str(num_points))  # Trigger count = # sweep points.
    keithley.write(':SOUR:DEL %g' % source_measure_delay)  # 50ms source delay.

    keithley.write(':OUTP ON')  # Turn on source output.

    data = keithley.query_ascii_values(':READ?', container=np.array)  # Trigger sweep, request data.

    # --- POST-PROCESSING
    data_elements = keithley.query(':FORMat:ELEMents:SENSe?')
    keithley.write(':OUTP OFF')  # End example given in manual

    # Data analysis

    print("Data Elements " + data_elements)
    data_struct = np.reshape(data, (num_points, num_elements))

    samples = len(data_struct[:, idxT])
    sampling_time = data_struct[-1, idxT] - data_struct[0, idxT]
    sampling_rate = np.round(sampling_time / samples, 5)
    print("Sampling Rate: {}".format(np.round(sampling_rate, 4)))
    print("Time to sample 100 points: {}".format(np.round(sampling_rate * 100, 3)))
    print("Time to sample 500 points: {}".format(np.round(sampling_rate * 500, 3)))

    # ---

    # - PLOTTING

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
    arr_T2, arr_V2 = list(zip(*sorted(zip(arr_T2,arr_V2))))

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
    ax1.legend(title='sampling time and rate (s)',
               title_fontsize='small', fontsize='small')

    ax2.plot(arr_T, arr_I, 'o', ms=ms_sample)
    ax2.set_xlabel('TSTamp (s)')
    ax2.set_ylabel('CURRent (A)')
    ax2.grid(alpha=0.25)

    ax3.plot(arr_V, arr_I, 'o', ms=ms_sample)
    ax3.set_xlabel('VOLTage (V)')
    ax3.set_ylabel('CURRent (A)')
    ax3.grid(alpha=0.25)

    plt.suptitle('External List: ( :SOUR:VOLT:MODE LIST )')
    plt.tight_layout()
    if save_fig:
        plt.savefig(join(path_results, save_id + '.png'), dpi=300)
    plt.show()
    plt.close()

    # save data
    df = pd.DataFrame(data_struct, columns=data_elements.split(','))
    df.to_excel(join(path_results, save_id + '.xlsx'))
