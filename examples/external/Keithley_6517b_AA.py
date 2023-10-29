import pyvisa
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

# reset
k3.write('*RST')

# configure: system
k3.write(':SYST:RNUM:RES')  # reset reading number to zero
k3.write(':SYST:ZCOR ON')   # Enable (ON) or disable (OFF) zero correct (default: OFF)
k3.write(':SYST:ZCH OFF')   # Enable (ON) or disable (OFF) zero check (default: OFF)

# configure: buffer
k3.write(':DISP:ENAB ON')   # Enable or disable the front-panel display
k3.write(':SENS:FUNC "CURR"')  # 'VOLTage[:DC]', 'CURRent[:DC]', 'RESistance', 'CHARge' (defulat='VOLT:DC')

k3.write(':SYST:TSC ON')    # Enable or disable external temperature readings (default: ON)
k3.write(':UNIT:TEMP C')    # Set temp. reading units

k3.write(':SYST:TST:TYPE REL')  # Configure timestamp type: RELative or RTClock
k3.write(':SYST:TST:REL:RES')   # Reset relative timestamp to zero seconds
k3.write(':TRAC:TST:FORM ABS')  # Select timestamp format for buffer readings: ABSolute or DELTa
k3.write(':TRAC:ELEM TST,VSO,CHAN')  # Select reading elements: NONE, VSOurce, TSTamp, HUMidity, CHANnel, ETEMPerature

k3.write(':FORM:DATA ASCii')  # Select data format: ASCii, REAL, SREal, DREal
k3.write(':FORM:ELEM READ,TST,RNUM,ETEM,VSO')  # data elements: VSOurce, READing, CHANnel, RNUMber, UNITs, TSTamp, STATus, ETEM, HUM

if bufStor:
    k3.write(':TRAC:FEED:CONT ALW')    # Select buffer control mode (NEVer, NEXT, ALWays, PRETrigger)
    k3.write(':TRAC:POIN MAX')  # Specify size of buffer: <n> or ':AUTO ON' to enable automatic buffer sizing
    k3.write(':TRAC:CLE')       # Clear readings from buffer
else:
    k3.write(':TRAC:FEED:CONT NEV')  # Select buffer control mode (NEVer = no readings stored in buffer)

# k3.write(':TRIG:COUN INF')    # Set measure count (1 to 99999 or INF) (preset: INF; Reset: 1)
# k3.write(':TRIG:SOUR IMM')    # Select control source (HOLD, IMMediate, TIMer, MANual, BUS, TLINk, EXTernal) (default: IMM)

if I_autorange == 1:
    k3.write(':SENS:CURR:RANG:AUTO ON')
else:
    k3.write(':SENS:CURR:RANG ' + str(I_range))

k3.write(':SOUR:VOLT:RANG ' + str(vout))

"""
%% splitter function
if splitter
    fprintf(obj6517,[':ROUT:SCAN:INT (@', channels, ')']);
    fprintf(obj6517,':ROUT:SCAN:STIM 0');  	% settling time = x.x sec
    fprintf(obj6517,':ROUT:SCAN:SMET CURR');   % to scan CURR/VOLT
    fprintf(obj6517,':ROUT:SCAN:VSL 0');      	% 1: Sets V-source limit to 200V
    fprintf(obj6517,':ROUT:SCAN:LSEL INT'); % initiate scan
end
"""

k3.write(':SENS:CURR:NPLC 1')

k3.write(':SOUR:VOLT ' + str(vout))
k3.write('OUTP ON')  # start voltage
k3.write(':INIT:CONT ON')  # start reading current (continuous initiation)

# k3.write(':FETC?')  # :FETCh? / :DATA:FRESh? / TRACe:DATA? -> get last / new reading / all readings
# data = k3.read()
data = k3.query_ascii_values(':FETCh?', container=np.array)  # ASCii string in order: READing,TSTamp,CHANnel,VSOurce
print(data)

# if you want to terminate scan
k3.write(':SOUR:VOLT 0')
k3.write(':ROUT:SCAN:LSEL NONE')

# end
k3.write(':OUTP OFF')  # turn output off
k3.write('*RST')  # reset GPIB to default
k3.close()