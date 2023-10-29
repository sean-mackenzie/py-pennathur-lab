import pyvisa
import time
import numpy as np

# inputs

# Keithley 6517b
GPIB = 27
BoardIndex = 3

I_autorange = 0     # 1 = autorange; 0 = I_range
I_range = 2e-3      # CURRent RANGe = 2 mA
vout = 1            # VOLTage = 1 V
splitter = 0        # 1 = use splitter card; 0 = no splitter card
bufStor = 1         # 1 = enable buffer storage; 0 = disable buffer storage
speed = 1           # Integration time in power line cycles (1: 1PLC (~10/s), 2: 0.1PLC (~20/s), 3: 0.01PLC

# open instrument
rm = pyvisa.ResourceManager()
k3 = rm.open_resource('GPIB{}::{}::INSTR'.format(BoardIndex, GPIB))

# ---

k3.write('*RST')
time.sleep(0.5)

# reset STATUS subsystem (which is not affected by *RST)
k3.write(':stat:pres;*cls')
k3.write(':stat:meas:enab 512')
k3.write(':*sre 1')
time.sleep(0.5)

k3.write(':FORM:ELEM READ,STAT,RNUM,TST,VSO')  # READ, STAT, RNUM are always in the buffer so they must be included
k3.write(':TRIG:COUN 20')
k3.write(':TRAC:POIN 20')
k3.write(':TRAC:ELEM TST,VSO')  # TST and VSO are optional but if included here, then also include in FORM:ELEM
k3.write(':trac:feed:cont next')

# Execute configured measurement

k3.write('OUTP ON')         # Turn source ON
k3.write(':INIT')           # Move from IDLE state to ARM Layer 1

time.sleep(2)                 # add delay to watch triggers sequentially unlatch

# request readings
try:
    # data = k3.query_ascii_values(':TRAC:DATA?')  # Read all readings from the buffer; ASCii string order: READing,TSTamp,CHANnel,VSOurce
    data = k3.query(':TRAC:DATA?')
    # data = k3.query_ascii_values(':FETCh?')
    # data = k3.query(':FETCh?')
    # :FETCh?       -->     Gets only the last singular data point from each ELEM (i.e., 1xN array).
    # :TRACe:DATA?  -->     Gets all readings in the buffer (i.e., M * (1xN) array).
    # :DATA:FRESh?  -->     Gets only "new" readings?
    data = data.split(',')
    print(len(data))
except pyvisa.errors.VisaIOError:
    print('No data return within timeout')

# if you want to terminate scan
k3.write(':SOUR:VOLT 0')            # Set voltage level to 0

# turn off and close instrument
k3.write(':OUTP OFF')  # turn output off
k3.write('*RST')  # reset GPIB to default
k3.close()