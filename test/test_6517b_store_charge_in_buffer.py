from os.path import join
import os
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pymeasure.instruments.keithley import Keithley6517B
import pyvisa

dict_ascii_lut = {
    'VDC': 'Volts',
    'ADC': 'Amps',
    'OHM': 'Ohms',
    'COUL': 'Coulombs',
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

def plot_data(df, save_dir, save_id, **kwargs,):

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

def package_data_and_export(df, df_settings, save_dir, save_id, **kwargs):
    file = join(save_dir, '{}_data.xlsx'.format(save_id))
    sns, dfs = ['data', 'settings'], [df, df_settings]
    idx, lbls = [False, True], [None, 'k']
    with pd.ExcelWriter(file) as writer:
        for sheet_name, dataframe, idx, idx_lbl in zip(sns, dfs, idx, lbls):
            dataframe.to_excel(writer, sheet_name=sheet_name, index=idx, index_label=idx_lbl)

def post_process_data(data, data_elements, dict_settings, save_dir, save_id, **kwargs,):
    df = parse_ascii(d=data, e=data_elements, as_type='pd.DataFrame')
    df_settings = pd.DataFrame.from_dict(data=dict_settings, orient='index')
    package_data_and_export(df, df_settings, save_dir, save_id)
    plot_data(df, save_dir, save_id)


# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------

def calculate_capacitance(q1, q2, v1, v2):
    return (q2 - q1) / (v2 - v1)


if __name__ == "__main__":
    rm = pyvisa.ResourceManager()
    check_inst = False  # True False
    if check_inst is True:
        print(rm.list_resources())  # only list "::INSTR" resources
        raise ValueError("Check instruments are connected.")

    # --- HARDWARE SETUP
    # Keithley 6517 electrometer used as voltage source and coulomb meter
    K1_BOARD_INDEX, K1_GPIB, K1_INST = 2, 27, '6517b'

    # ---

    # root test subject
    BASE_DIR = r'C:\Users\nanolab\Box\2024\zipper_paper\Methods\CapacitanceMeasurements'
    TEST_TYPE = 'CAPACITANCE'
    TEST_SUBJECT = '3.3nF'
    RESISTOR_IN_SERIES = 474e3  # Ohms
    R_LABEL = 'R_474kOhms'
    second_pass_modifiers = True  # True False
    """ 
    second pass modifiers are additional features that I added to the original code.
    They were shown here to work, so I will leave them for future reference. 

    NOTE: some things I found out running other scripts:
        * This code will only work if NPLC < 0.46. 
            Otherwise, you will get a timeout error, regardless of how long you set the timeout to. I think this is related
             to :LSYNC, maybe because :LYSNC OFF doesn't work if NPLC >= 0.5. 
        * This code will not work if LSYNC is enabled. 
            Regardless of the NPLC or timeout. 
    """
    # ---
    TID = 110
    SOURCE_VOLTAGE = 101  # voltage
    SENSE_FUNC = 'CHAR'  # 'RES', 'CURR', 'CHAR'
    SENSE_NPLC = 0.15  # 0.01 to 10
    SENSE_NUM_SAMPLES = 400
    #SENSE_USE_REFERENCE = None  # 'CHAR', 'ZCOR', or None
    #SENSE_RANGE_AUTO = 'OFF'
    SENSE_RANGE = 2e-6  # Coulombs: 0 to 2e6

    # ---

    SLEEP_ORDER = 'INIT+SOURCE 0V+START BUFFER, SOURCE {}V, SOURCE 0V'.format(SOURCE_VOLTAGE)
    SLEEP_AFTER_INIT = 0.25
    SLEEP_AFTER_SOURCE_V = 2.0
    SLEEP_AFTER_SOURCE_0V = 2.0

    # ---
    SAVE_ID = '{}_tid{}_{}V_{}NPLC_test-{}'.format(R_LABEL, TID, SOURCE_VOLTAGE, SENSE_NPLC, TEST_TYPE)
    SAVE_DIR = join(BASE_DIR, TEST_SUBJECT)
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    DICT_SETTINGS = {
        'save_id': SAVE_ID,
        'save_dir': SAVE_DIR,
        'test_type': TEST_TYPE,
        'test_subject': TEST_SUBJECT,
        'resistor_in_series': RESISTOR_IN_SERIES,
        'r_label': R_LABEL,
        'tid': TID,
        'source_voltage': SOURCE_VOLTAGE,
        'sense_func': SENSE_FUNC,
        'sense_nplc': SENSE_NPLC,
        'sense_num_samples': SENSE_NUM_SAMPLES,
        'sense_range': SENSE_RANGE,
        'sleep_order': SLEEP_ORDER,
        'sleep_after_init': SLEEP_AFTER_INIT,
        'sleep_after_source_v': SLEEP_AFTER_SOURCE_V,
        'sleep_after_source_0v': SLEEP_AFTER_SOURCE_0V,
    }

    # ------------------------------------------------------------------------------------------------------------------
    # SETUP KEITHLEY
    # ------------------------------------------------------------------------------------------------------------------

    # Replace 'GPIB::24' with your instrument's address
    keithley = Keithley6517B("GPIB{}::{}::INSTR".format(K1_BOARD_INDEX, K1_GPIB), timeout=5000)

    keithley.write('*RST')
    keithley.write(':SYST:ZCH ON')
    keithley.write(':FORMAT:ELEM READ')  # Store only the reading
    keithley.write(':FORMAT:DATA SRE')  # SREal: IEEE std 754 single-precision

    """ NOTE: I tried all of the below functions to increase the voltage range
    but it will not go above 200V, and, it seems to be +100V to -100V because
    I cannot apply 101 V. """
    # keithley.write(':SOUR:VOLT ' + str(SOURCE_VOLTAGE))
    #keithley.write(':SOUR:VOLT:RANG 1000')
    #keithley.write(':SOUR:VOLT:LIM 250')
    #keithley.write(':SOUR:VOLT:LIM:STAT ON')
    # keithley.auto_range_source()
    # keithley.source_voltage_range = 1000
    print(keithley.ask(':VOLT:RANG?'))
    # raise ValueError("stop here")
    keithley.write(':SOUR:VOLT 0')

    if SENSE_FUNC == 'CHAR':
        keithley.write(':SENSE:FUNC "CHAR"')
        keithley.write(':CHAR:RANGE ' + str(SENSE_RANGE))
        keithley.write(':CHAR:NPLC ' + str(SENSE_NPLC))
        # raise ValueError("stop here")

        #keithley_inst.write(':SENS:FUNC "CHAR"')  # 'CHARge'
        #keithley_inst.write(':CHAR:NPLC ' + str(settings['sense_nplc']))  # NPLC: 0.01 to 10
        #keithley_inst.write(':CHAR:RANG ' + str(settings['sense_range']))  # RANGe: 0 to 2e-6
        #keithley_inst.write(':CHAR:RANG:AUTO ' + str(settings['sense_range_auto']))  # OFF or ON

    elif SENSE_FUNC == 'CURR':
        keithley.write(':SENSE:FUNC "{}"'.format(SENSE_FUNC))
        keithley.write(':SENSE:CURR:RANGE {}' + str(SENSE_RANGE))
        keithley.write(':SENSE:CURR:NPLC {}' + str(SENSE_NPLC))
    elif SENSE_FUNC == 'VOLT':
        keithley.write(':SENSE:FUNC "{}"'.format(SENSE_FUNC))
        keithley.write(':SENSE:VOLT:RANGE {}' + str(SENSE_RANGE))
        keithley.write(':SENSE:VOLT:NPLC {}' + str(SENSE_NPLC))
    elif SENSE_FUNC == 'RES':
        keithley.write(':SENSE:FUNC "RES"')
        keithley.write(':RES:RANGE ' + str(SENSE_RANGE))
        keithley.write(':RES:NPLC ' + str(SENSE_NPLC))
    else:
        raise ValueError("Sense function not understood.")
    #keithley.write(':SENS:VOLT:AVERAGE:TYPE NONE')
    #keithley.write(':SENS:VOLT:MED:STAT OFF')
    keithley.write(':DISP:ENABLE OFF')  # originally, ON
    keithley.write(':SYST:ZCH OFF')
    keithley.write(':SYST:LSYNC:STAT 0')  # disable power line synchronization

    keithley.write(':TRACE:FEED:CONT NEVER')  # disable buffer reading
    keithley.write(':TRACE:CLEAR')  # clear buffer

    if second_pass_modifiers:
        keithley.write(':TRACE:ELEM TST,VSO')  # data elements
    else:
        keithley.write(':TRACE:ELEM NONE')  # data store elements: NONE
    keithley.write(':TRACE:POINTS ' + str(SENSE_NUM_SAMPLES))
    keithley.write(':TRIG:COUNT ' + str(SENSE_NUM_SAMPLES))
    keithley.write(':TRIG:DELAY 0')
    keithley.write(':TRACE:FEED:CONT NEXT')  # specify buffer control: fill and stop.

    # ------------------------------------------------------------------------------------------------------------------
    # EXECUTE MEASUREMENT
    # ------------------------------------------------------------------------------------------------------------------

    keithley.write(':INIT')
    keithley.write(':OUTP ON')
    # -
    # NOTE: THIS STATEMENT TELLS THE KEITHLEY TO START BUFFER READINGS!
    print("Buffer points: {}".format(keithley.buffer_points))
    # print("resistance: {}".format(keithley.resistance))
    # -
    time.sleep(SLEEP_AFTER_INIT)

    keithley.write(':SOUR:VOLT ' + str(SOURCE_VOLTAGE))
    time.sleep(SLEEP_AFTER_SOURCE_V)

    keithley.write(':SOUR:VOLT 0')
    time.sleep(SLEEP_AFTER_SOURCE_0V)

    keithley.stop_buffer()  # Stop storing readings
    """ Aborts the buffering measurement, by stopping the measurement
    arming and triggering sequence. """
    # self.write(":ABOR")

    if second_pass_modifiers:
        # NOTE: READ, STAT, RNUM, and UNIT are always enabled for the buffer and are included in the response for :ELEM?
        keithley.write(':FORM:ELEM READ,STAT,RNUM,UNIT,TST,VSO')  # data elements

        # Read data from buffer
        # data = keithley.buffer_data
        #   def buffer_data(self):
        """     Get a numpy array of values from the buffer. """


        #       self.write(":FORM:DATA ASCII")
        #       return np.array(self.values(":TRAC:DATA?"), dtype=np.float64)
        def read_buffer_data(inst):
            inst.write(":FORM:DATA ASCII")
            return inst.ask(":TRAC:DATA?")  # inst.values(":TRAC:DATA?")


        DATA = read_buffer_data(inst=keithley)
        print("Buffer: {}".format(DATA))

    else:
        # Read data from buffer
        DATA = keithley.buffer_data
        """ Get a numpy array of values from the buffer. """
        #self.write(":FORM:DATA ASCII")
        #return np.array(self.values(":TRAC:DATA?"), dtype=np.float64)
        print("Buffer: {}".format(DATA))

        print("Readings from Buffer:")
        for i, reading in enumerate(DATA):
            print("{}: {}".format(i, reading))

    keithley.write(':OUTP OFF')

    DATA_ELEMENTS = keithley.ask(':FORM:ELEM?')  #  'READ,STAT,RNUM,UNIT,TST,VSO'  # data elements

    # ------------------------------------------------------------------------------------------------------------------
    # POST-PROCESS
    # ------------------------------------------------------------------------------------------------------------------

    # -
    # --- parse, package, and export
    # data_elements = k1.query(':FORMat:ELEM?')
    post_process_data(
        data=DATA,
        data_elements=DATA_ELEMENTS,
        dict_settings=DICT_SETTINGS,
        save_dir=SAVE_DIR,
        save_id=SAVE_ID,
    )


    print("Completed without errors.")