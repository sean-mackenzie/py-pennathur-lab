import os
from os.path import join
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pyvisa
import time







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
    K1_GPIB, K1_BOARD_INDEX = 27, 2


    # ---

    # 0. Setup charge measurement function

    # 1. Zero charge immediately before measure

    # 2. Turn on voltage source (i.e., apply a step voltage)

    # 3. Measure charge immediately after voltage step

    # 4. Calculate capacitance from step voltage and charge measurement

    CAPACITANCE = calculate_capacitance(q1=0, q2=1, v1=0, v2=10)

    # 5. Set voltage to 0 to dissipate charge from capacitor

    #6. (Not instructed in manual but maybe?) Measure charge dissipation from capacitor


    # ---

    print("Script completed without errors.")