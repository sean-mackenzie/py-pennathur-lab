import os
from os.path import join

import pandas as pd
import pyvisa
import time
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

def setup_2410_trigger(keithley_inst, voltage):
    delay = 0.05


    # - set up trigger keithley
    keithley_inst.write('*RST')  # Restore GPIB default
    keithley_inst.write(':FORMat:ELEMents:SENSe VOLTage, CURRent, TIME')
    keithley_inst.write(':DATA:TSTamp:FORMat DELTa')
    keithley_inst.write(':SOUR:FUNC VOLT')  # Volts source function.
    keithley_inst.write(':SOUR:VOLT:RANG 1')  # Select V-source range (n = range).
    keithley_inst.write(':SENS:FUNC "CURR:DC"')  # Current sense function.
    keithley_inst.write(':SENS:CURR:PROT %g' % 20e-3)  # 1 mA current compliance.
    keithley_inst.write(':SENS:CURR:RANG %g' % 10e-3)  # 1 mA current compliance.
    keithley_inst.write(':SENS:CURR:NPLC %g' % 10)  # Specify integration rate (in line cycles): [0.01 to 10E3] (default = 1)

    keithley_inst.write(':SOUR:VOLT:MODE FIX')  # List volts sweep mode.
    keithley_inst.write(':SOUR:LIST:VOLT ' + str(voltage))  # List sweep points.
    keithley_inst.write(':TRIG:COUN 1')  # Trigger count = # sweep points.
    keithley_inst.write(':SOUR:DEL %g' % delay)  # 50ms source delay.


if __name__ == "__main__":

    # --- SETUP
    rm = pyvisa.ResourceManager()
    check_inst = False  # True False
    if check_inst is True:
        print(rm.list_resources())  # only list "::INSTR" resources
        # # returns something like: ('ASRL1::INSTR', 'ASRL2::INSTR', 'GPIB0::14::INSTR')
        raise ValueError("Check instruments are connected.")

    k1_source_GPIB, k1_source_board_index = 25, 1  # Keithley: source measure unit

    # --- INPUTS

    wid = 'C19-30pT_20nmAu'
    path_results = r'C:\Users\nanolab\Box\2024\zipper_paper\Methods\Keithley 2410 4-Wire\{}'.format(wid)
    if not os.path.exists(path_results):
        os.makedirs(path_results)

    prog_ = 'AUTO'  # 'AUTO' or 'MAN'
    test_id = 6
    save_id = '{}_tid{}'.format(prog_, test_id)

    # ------------------
    single_point_max = True
    sc = 10
    start, stop, step = 0.1 * sc, 0.5 * sc, 0.025 * sc
    values = np.arange(start, stop + step / 4, step)
    values_lst = numpy_array_to_string(values)
    num_points = len(values)
    source_measure_delay = 0.10  # (s)
    nplc = 10
    ohms_range = 1e6
    elements_sense = 'VOLTage, CURRent, TIME, RESistance'  # STATus

    # ------------------

    # Initialize instruments
    k1 = rm.open_resource('GPIB{}::{}::INSTR'.format(k1_source_board_index, k1_source_GPIB))

    # - set up source keithley
    k1.write('*RST')  # Restore GPIB default
    k1.timeout = 8000  # Set the timeout error time (units: ms) for PyVISA
    # print("Estimated timeout: {} s".format(estimated_timeout / 1000))

    if prog_ == 'AUTO':
        k1.write(':SENS:FUNC "RES"')
        k1.write(':SENS:RES:MODE AUTO')
        k1.write(':SENS:RES:NPLC ' + str(nplc))
        k1.write(':SYST:RSEN ON')
        k1.write(':FORM:ELEM RES')
        k1.write(':OUTP ON')
        data = k1.query(':READ?')
        k1.write(':OUTP OFF')
        data_elem = k1.query(':FORM:ELEM?')
    elif prog_ == 'MAN':
        k1.write(':SENS:FUNC "RES"')
        k1.write(':SENS:RES:MODE MAN')
        k1.write(':SENS:RES:RANG ' + str(ohms_range))
        k1.write(':SENS:RES:NPLC ' + str(nplc))
        k1.write(':SENS:VOLT:PROT ' + str(np.max(values)))
        k1.write(':SENS:CURR:PROT 20E-3')

        # keithley.write(':SENS:FUNC:CONC OFF')  # Turn off concurrent functions.
        k1.write(':SOUR:FUNC VOLT')  # Volts source function.
        k1.write(':SOUR:VOLT:RANG ' + str(np.max(values)))  # Select V-source range (n = range).
        k1.write(':SOUR:VOLT:MODE LIST')  # List volts sweep mode.
        k1.write(':SOUR:LIST:VOLT ' + values_lst)  # List sweep points.
        k1.write(':TRIG:COUN ' + str(num_points))  # Trigger count = # sweep points.
        k1.write(':SOUR:DEL %g' % source_measure_delay)  # 50ms source delay.

        k1.write(':SYST:RSEN ON')
        k1.write(':FORM:ELEM VOLT,CURR,RES,TIME')
        #k1.write(':DATA:TSTamp:FORMat DELTa')

        k1.write(':OUTP ON')
        # data = k1.query(':READ?')
        data = k1.query_ascii_values(':READ?', container=np.array)  # request data.
        k1.write(':OUTP OFF')
        data_elem = k1.query(':FORM:ELEM?')
    else:
        raise ValueError("Check program setting.")

    print(data_elem)
    print(data)
    k1.close()

    if prog_ == 'AUTO':
        dict_res = {
            'prog': prog_,
            'test_id': test_id,
            'save_id': save_id,
            'RES': data,
        }
        df = pd.DataFrame.from_dict(data=dict_res, orient='index')
        df.to_excel(join(path_results, '{}_4-wire.xlsx'.format(save_id)))
    else:
        # post-process stimulus data
        data_struct = np.reshape(data, (num_points, len(data_elem.split(','))))
        df = pd.DataFrame(data_struct, columns=data_elem.split(','))
        df.to_excel(join(path_results, '{}_4-wire.xlsx'.format(save_id)))

        """
        file = join(settings['save_dir'], '{}_data.xlsx'.format(settings['save_id']))
        sns, dfs = ['data', 'settings'], [df, df_settings]
        idx, lbls = [False, True], [None, 'k']
        with pd.ExcelWriter(file) as writer:
            for sheet_name, dataframe, idx, idx_lbl in zip(sns, dfs, idx, lbls):
                dataframe.to_excel(writer, sheet_name=sheet_name, index=idx, index_label=idx_lbl)
        """

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(df['VOLT'], df['RES'], 'o-', label='data')
        ax.set_xlabel('Voltage (V)')
        ax.set_ylabel('Resistance (Ohms)')
        fig.savefig(join(path_results, '{}_4-wire.png'.format(save_id)))
        plt.show()
        plt.close(fig)