from os.path import join

import pandas as pd
import pyvisa
import numpy as np
import matplotlib.pyplot as plt
import time
from datetime import datetime

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
    check_inst = False  # True False
    if check_inst is True:
        rm = pyvisa.ResourceManager()
        print(rm.list_resources())  # only list "::INSTR" resources
        raise ValueError("Check instruments are connected.")

    # --- INPUTS

    path_results = r'C:\Users\nanolab\Desktop\sean\05312025_W13_Pads-Only\DielectricAbsorption'
    tid = 16
    V_soak = -250  # Volts
    test_type = 1
    save_id = 'tid{}_B3_{}V_5NPLC'.format(tid, V_soak)
    save_fig = True

    # Get current time
    current_time = datetime.now()
    time_started = current_time.strftime('%H:%M:%S')

    BOARD_INDEX = 1
    GPIB = 25


    # ------------------------------------------------------------------------------------------------------------------
    # SHOULD NOT NEED TO MODIFY SCRIPT BELOW
    # ------------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    """
    # DIELECTRIC ABSORPTION TEST SEQUENCE
    # 1. Apply soak voltage for soak interval ("typically" 1-2 minutes, but experiments ~10 s)
    V_soak = 10  # Volts
    t_soak = 5  # seconds
    I_soak_compliance = 1e-3  # Amps
    # -
    # 2. Output 0 V with compliance of 100 mA for discharge interval
    V_discharge = 0  # Volts
    t_discharge = 5  # seconds
    I_discharge_compliance = 100e-3  # Amps
    # -
    # 3. Output a current of 0 A on as low a current range as possible and measure voltage
    I_residual = 0  # Amps
    t_residual = 10  # seconds
    I_range = 1e-6  # Amps (manual says 1 uA is lowest source current range)
    """
    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    # --- KEITHLEY CODE
    estimated_timeout = 35 * 1000  # num_points * source_measure_delay * 1000 * 2 + 0.2  # (ms)
    # DATA TYPES
    elements_sense = 'VOLTage, CURRent, TIME'  #, RESistance, STATus
    idxV, idxC, idxT, idxR, idxSTAT = 0, 1, 2, 3, 4
    num_elements = len(elements_sense.split(','))

    # ---

    rm = pyvisa.ResourceManager()
    # keithley = rm.open_resource("GPIB::{}".format(GPIB))
    keithley = rm.open_resource("GPIB{}::{}::INSTR".format(BOARD_INDEX, GPIB), timeout=5000)

    # 0.
    keithley.write('*RST')  # Restore GPIB default
    keithley.timeout = estimated_timeout  # Set the timeout error time (units: ms) for PyVISA
    print("Estimated timeout: {} s".format(estimated_timeout / 1000))

    keithley.write(':FORMat:ELEMents:SENSe ' + elements_sense)
    keithley.write(':DATA:TSTamp:FORMat DELTa')

    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # DIELECTRIC ABSORPTION TEST SEQUENCE
    # 1. Apply soak voltage for soak interval ("typically" 1-2 minutes, but experiments ~10 s)
    # V_soak = 0  # Volts
    t_soak = 5  # seconds
    I_soak_compliance = 1e-3  # Amps
    # -
    V_soak_num_points = 80
    V_soak_values = np.ones(V_soak_num_points) * V_soak
    V_soak_values[0:5] = 0
    V_soak_values[-10:] = 0
    #V_soak_values_ramp_down = np.array([V_soak / 2, V_soak / 4, 0, 0, 0])
    #V_soak_values = np.hstack((V_soak_values, V_soak_values_ramp_down))
    #V_soak_num_points = len(V_soak_values)
    V_soak_range = V_soak + 5
    I_soak_range = 1e-6  # Amps
    I_soak_NPLC = 10  # number of power line cycles (integration period = NPLC / 60)
    I_soak_delay = 0.0  # seconds
    # -
    # keithley.write(':SENS:FUNC:CONC OFF')  # Turn off concurrent functions.
    keithley.write(':SOUR:FUNC VOLT')  # Volts source function.
    keithley.write(':SOUR:VOLT:RANG %g' % V_soak_range)  # Select V-source range (n = range).
    keithley.write(':SENS:FUNC "CURR:DC"')  # Current sense function.
    keithley.write(':SENS:CURR:PROT %g' % I_soak_range)  # 1 mA current compliance.
    keithley.write(':SENS:CURR:RANG %g' % I_soak_range)  # 1 mA current compliance.
    keithley.write(':SENS:CURR:NPLC %g' % I_soak_NPLC)  # Specify integration rate (in line cycles): [0.01 to 10E3] (default = 1)
    keithley.write(':SOUR:VOLT:MODE LIST')  # List volts sweep mode.
    keithley.write(':SOUR:LIST:VOLT ' + numpy_array_to_string(V_soak_values))  # List sweep points.
    keithley.write(':TRIG:COUN ' + str(V_soak_num_points))  # Trigger count = # sweep points.
    keithley.write(':SOUR:DEL %g' % I_soak_delay)  # 50ms source delay.
    keithley.write(':OUTP ON')  # Turn on source output.
    data1 = keithley.query_ascii_values(':READ?', container=np.array)  # Trigger sweep, request data.
    print(np.shape(data1))
    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # 2. Output 0 V with compliance of 100 mA for discharge interval
    V_discharge = 0  # Volts
    t_discharge = 5  # seconds
    I_discharge_compliance = 100e-3  # Amps
    # -
    I_discharge_NPLC = 10
    # -
    # keithley.write(':SENS:FUNC:CONC OFF')  # Turn off concurrent functions.
    # keithley.write(':SOUR:FUNC VOLT')  # Volts source function.
    keithley.write(':SOUR:VOLT:MODE FIXed')  # List volts sweep mode.
    keithley.write(':SOUR:VOLT %g' % V_discharge)  # List sweep points.
    keithley.write(':SOUR:VOLT:RANG 1')  # Select V-source range (n = range).
    # keithley.write(':SENS:FUNC "CURR:DC"')  # Current sense function.
    keithley.write(':SENS:CURR:PROT %g' % I_discharge_compliance)  # 1 mA current compliance.
    keithley.write(':SENS:CURR:RANG %g' % I_discharge_compliance)  # 1 mA current compliance.
    # keithley.write(':SENS:CURR:NPLC %g' % I_discharge_NPLC)  # Specify integration rate (in line cycles): [0.01 to 10E3] (default = 1)
    # keithley.write(':TRIG:COUN ' + str(num_points))  # Trigger count = # sweep points.
    # keithley.write(':SOUR:DEL %g' % source_measure_delay)  # 50ms source delay.
    # keithley.write(':OUTP ON')  # Turn on source output.
    # data = keithley.query_ascii_values(':READ?', container=np.array)  # Trigger sweep, request data.
    print("DISCHARGING!")
    time.sleep(t_discharge)
    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # 3. Output a current of 0 A on as low a current range as possible and measure voltage
    I_residual = 0  # Amps
    t_residual = 10  # seconds
    I_residual_range = 1e-6  # Amps (manual says 1 uA is lowest source current range)
    # -
    V_residual_NPLC = 5
    V_residual_delay = 0.0  # seconds (originally: 0.05)
    V_residual_num_points = 100  # I think 100-110 is the max list size
    I_residual_values = np.ones(V_residual_num_points) * I_residual
    integration_period = V_residual_NPLC / 60
    # -
    # keithley.write(':SENS:FUNC:CONC OFF')  # Turn off concurrent functions.
    keithley.write(':SOUR:FUNC CURR')  # Volts source function.
    keithley.write(':SOUR:CURR:RANG MIN')  # Select V-source range (n = range).
    keithley.write(':SENS:FUNC "VOLT:DC"')  # Current sense function.
    keithley.write(':SENS:VOLT:PROT 20')  # 1 mA current compliance.
    keithley.write(':SENS:VOLT:RANG 20')  # 1 mA current compliance.
    keithley.write(':SENS:VOLT:NPLC %g' % V_residual_NPLC)  # Specify integration rate (in line cycles): [0.01 to 10E3] (default = 1)
    keithley.write(':SOUR:CURR:MODE LIST')  # List volts sweep mode.
    keithley.write(':SOUR:LIST:CURR ' + numpy_array_to_string(I_residual_values))  # List sweep points.
    keithley.write(':TRIG:COUN ' + str(V_residual_num_points))  # Trigger count = # sweep points.
    keithley.write(':SOUR:DEL %g' % V_residual_delay)  # 50ms source delay.
    keithley.write(':OUTP ON')  # Turn on source output.
    data = keithley.query_ascii_values(':READ?', container=np.array)  # Trigger sweep, request data.
    # ------------------------------------------------------------------------------------------------------------------
    data = np.hstack((data1, data))
    num_points_total = V_soak_num_points + V_residual_num_points
    # ------------------------------------------------------------------------------------------------------------------

    # --- POST-PROCESSING
    data_elements = keithley.query(':FORMat:ELEMents:SENSe?')
    keithley.write(':OUTP OFF')  # End example given in manual

    # Data analysis

    print("Data Elements " + data_elements)
    data_struct = np.reshape(data, (num_points_total, num_elements))

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
    time_split = 43
    arr_V_left = arr_V[arr_T < time_split]
    arr_T_left = arr_T[arr_T < time_split]
    ax1.plot(arr_T_left, arr_V_left, 'o', ms=ms_sample, color='tab:red', label='')
    # ax1.plot(arr_T2, arr_V2, lw=lw_time, marker=mkr_time, ms=ms_time, color='gray')
    ax1.set_xlabel('TSTamp (s)')
    ax1.set_ylabel(r'$V_{charge} \: (V)$', color='tab:red')
    # ax1.grid(alpha=0.25)
    # ---
    arr_V_right = arr_V[arr_T > time_split]
    arr_T_right = arr_T[arr_T > time_split]
    ax1r = ax1.twinx()
    ax1r.plot(arr_T_right, arr_V_right, '-o', ms=ms_sample, color='tab:blue', label='')
    ax1r.set_ylabel(r'$V_{discharge} \: (V)$', color='tab:blue')
    ax1r.grid(alpha=0.25)

    ax2.plot(arr_T, arr_I, 'o', ms=ms_sample)
    ax2.set_xlabel('TSTamp (s)')
    ax2.set_ylabel('CURRent (A)')
    ax2.grid(alpha=0.25)

    ax3.plot(arr_V, arr_I, 'o', ms=ms_sample)
    ax3.set_xlabel('VOLTage (V)')
    ax3.set_ylabel('CURRent (A)')
    ax3.grid(alpha=0.25)

    # Get current time
    current_time = datetime.now()
    time_finished = current_time.strftime('%H:%M:%S')
    plt.suptitle(f'5/27/2025: Time started: {time_started}, finished: {time_finished}', fontsize=10)
    plt.tight_layout()
    if save_fig:
        plt.savefig(join(path_results, save_id + '.png'), dpi=300)
    plt.show()
    plt.close()

    # save data
    df = pd.DataFrame(data_struct, columns=data_elements.split(','))
    df.to_excel(join(path_results, save_id + '.xlsx'))
