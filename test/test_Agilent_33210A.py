import os
from os.path import join
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pyvisa
import time

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
    awg_GPIB, awg_board_index = 10, 0  # Arbitrary waveform generator (awg)

    # Initialize instruments
    awg = rm.open_resource('GPIB{}::{}::INSTR'.format(awg_board_index, awg_GPIB))
    awg.write('*RST')  # Restore GPIB default

    # Program physical/hardware set up
    awg.write('OUTP:LOAD INF')  # OUTPut:LOAD {<ohms>|INFinity|MINimum|MAXimum}

    awg_wave = 'SIN'  # SIN, SQU, RAMP, PULS, DC
    awg_freq = 100000  # 0.001 to 10000000
    awg_square_duty_cycle = 50  # 20 to 80 (square waves only)
    awg_volt_unit = 'VPP'  # VPP, VRMS
    Vapp, Voffset = 222, 0
    trek_ampli = 500
    awg_volt, awg_volt_offset = np.round(Vapp / trek_ampli, 3), np.round(Voffset / trek_ampli, 2)

    if awg_volt + awg_volt_offset > 18:
        raise ValueError("AWG max Vpp + Voffset is 20.")
    elif awg_volt > 18:
        raise ValueError("AWG max Vpp is 20.")
    else:
        print("AWG Voltage Output: {} {} + {} DC".format(awg_volt, awg_volt_unit, awg_volt_offset))


    # Program waveform
    awg.write('FUNC ' + awg_wave)  # FUNCtion {SINusoid|SQUare|RAMP|PULSe|NOISe|DC|USER}
    awg.write('FREQ ' + str(awg_freq))  # FREQuency {<frequency>|MINimum|MAXimum}
    awg.write('VOLT ' + str(awg_volt))  # VOLTage {<amplitude>|MINimum|MAXimum}
    awg.write('VOLT:OFFS ' + str(awg_volt_offset))  # VOLTage:OFFSet {<offset>|MINimum|MAXimum}
    awg.write('VOLT:UNIT ' + awg_volt_unit)  # VOLTage:UNIT {VPP|VRMS|DBM}
    awg.write('VOLT:RANG:AUTO ON')  # VOLTage:RANGe:AUTO {OFF|ON|ONCE}
    if awg_wave == 'SQU':
        awg.write('FUNC:SQU:DCYC ' + str(awg_square_duty_cycle))  # FUNCtion:SQUare:DCYCle {<percent>|MINimum|MAXimum}
    awg.write('OUTP ON')  # OUTPut {OFF|ON}

    time.sleep(2)

    awg.write('OUTP OFF')


    print("Completed without errors.")