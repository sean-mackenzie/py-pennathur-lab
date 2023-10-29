import pyvisa
import time
import numpy as np

# inputs

# Keithley 6517b
GPIB = 27
BoardIndex = 3

# Keithley Model 2361 Trigger Control Unit (TCU)
TCU_GPIB = 15
TCU_BoardIndex = 2

I_autorange = 0     # 1 = autorange; 0 = I_range
I_range = 2e-3      # CURRent RANGe = 2 mA
vout = 1            # VOLTage = 1 V
splitter = 0        # 1 = use splitter card; 0 = no splitter card
bufStor = 0         # 1 = enable buffer storage; 0 = disable buffer storage
speed = 1           # Integration time in power line cycles (1: 1PLC (~10/s), 2: 0.1PLC (~20/s), 3: 0.01PLC

# open instrument
rm = pyvisa.ResourceManager()
TCU = rm.open_resource('GPIB{}::{}::INSTR'.format(TCU_BoardIndex, TCU_GPIB))

# ---

# Set up TCU triggers

TCU.write('C0X')  # clear the present program
time.sleep(0.1)
for i in range(6):
    TCU.write('I{}X'.format(i + 1)) # unlatch all trigger channels
    time.sleep(0.5)                 # add delay to watch triggers sequentially unlatch
TCU.write('2>3')                    # if 2 triggered, trigger out 3
time.sleep(0.1)
# TCU.close()


# ---

# Keithley 6517b

# open instrument
k3 = rm.open_resource('GPIB{}::{}::INSTR'.format(BoardIndex, GPIB))

# RESET to defaults
k3.write('*RST')

# SYSTEM
k3.write(':SYST:RNUM:RES')  # reset reading number to zero
k3.write(':SYST:ZCOR ON')   # Enable (ON) or disable (OFF) zero correct (default: OFF)
k3.write(':SYST:ZCH OFF')   # Enable (ON) or disable (OFF) zero check (default: OFF)
k3.write(':DISP:ENAB ON')   # Enable or disable the front-panel display
k3.write(':SYST:TSC ON')    # Enable or disable external temperature readings (default: ON)
k3.write(':UNIT:TEMP K')    # Configure temperature units: C, CEL, F, FAR, K (default: C)
k3.write(':SYST:TST:TYPE REL')  # Configure timestamp type: RELative or RTClock
k3.write(':SYST:TST:REL:RES')   # Reset relative timestamp to zero seconds

# BUFFER
k3.write(':TRAC:CLE')           # Clear readings from buffer
k3.write(':TRAC:TST:FORM ABS')  # Select timestamp format for buffer readings: ABSolute or DELTa
k3.write(':TRAC:ELEM TST,VSO,CHAN')  # Select reading elements: NONE, VSOurce, TSTamp, HUMidity, CHANnel, ETEMPerature
if bufStor:
    k3.write(':TRAC:FEED:CONT ALW')    # Select buffer control mode (NEVer, NEXT, ALWays, PRETrigger)
    # k3.write(':TRAC:POIN <n>')      # Specify size of buffer
    k3.write(':TRAC:POIN MAX')  # Specify size of buffer: <n> or ':AUTO ON' to enable automatic buffer sizing
    k3.write(':TRAC:CLE')       # Clear readings from buffer
else:
    k3.write(':TRAC:FEED:CONT NEV')  # Select buffer control mode

# FORMAT
k3.write(':FORM:DATA ASCii')  # Select data format: ASCii, REAL, SREal, DREal
k3.write(':FORM:ELEM READ,TST,RNUM,ETEM,VSO')  # data elements: VSOurce, READing, CHANnel, RNUMber, UNITs, TSTamp, STATus, ETEM, HUM


# --- Define Trigger Model

# IDLE
k3.write(':INIT:CONT OFF')       # When instrument returns to IDLE layer, CONTINUOUS ON = repeat; OFF = hold in IDLE

# ARM LAYER 1 (Arm layer)
k3.write(':ARM:TCON:DIR ACCeptor')        # Wait for Arm Event (default: ACCeptor)
k3.write(':ARM:COUN 1')                   # Specify arm count: number of cycles around arm layer (default: 1)
k3.write(':ARM:SOUR IMM')                 # Select control source: IMM, TLINk or EXT. (default: IMM)
#k3.write(':ARM:LAYer1:TCON:ASYN:ILIN 2')    # Input line for asynchronous trigger (default: 2)
#k3.write(':ARM:LAYer1:TCON:ASYN:OLIN 1')    # Output line for asynchronous trigger (default: 1)

# ARM LAYER 2 (Scan layer)
k3.write(':ARM:LAYer2:TCON:DIR ACCeptor')   # Wait for Arm Event
k3.write(':ARM:LAYer2:COUN 1')              # Perform 1 arm layer cycle
k3.write(':ARM:LAYer2:SOUR IMM')            # Immediately go to Arm Layer 2
#k3.write(':ARM:LAYer2:TCON:ASYN:ILIN 2')    # Input line for asynchronous trigger (default: 2)
#k3.write(':ARM:LAYer2:TCON:ASYN:OLIN 1')    # Output line for asynchronous trigger (default: 1)
k3.write(':ARM:LAYer2:DEL 0')               # After receiving Arm Layer 2 Event, delay before going to Trigger Layer

# TRIGGER LAYER (Measure layer)
k3.write(':TRIG:TCON:DIR ACC')     # Wait for trigger event (TLINK)
k3.write(':TRIG:COUN 1')                # Set measure count (1 to 99999 or INF) (preset: INF; Reset: 1)
k3.write(':TRIG:SOUR TLIN')             # Select control source (HOLD, IMMediate, TIMer, MANual, BUS, TLINk, EXTernal) (default: IMM)
k3.write(':TRIG:TCON:PROT ASYN')        # ASYN = use separate trigger lines, SSYN = input/output use same trigger lines
k3.write(':TRIG:TCON:ASYN:ILIN 1')    # Input line for asynchronous trigger (default: 2)
k3.write(':TRIG:TCON:ASYN:OLIN 2')    # Output line for asynchronous trigger (default: 1)
k3.write(':TRIG:DEL 0')                  # After receiving Measure Event, delay before Device Action

# Set up Source functions
k3.write(':SOUR:VOLT 1')            # Define voltage level: -1000 to +1000 V (default: 0)
k3.write(':SOUR:VOLT:RANG 100')     # Define voltage range: <= 100: 100V, >100: 1000 V range (default: 100 V)
k3.write(':SOUR:VOLT:LIM 1000')     # Define voltage limit: 0 to 1000 V (default: 1000 V)

# Set up Sense functions
k3.write(':SENS:FUNC "CURR"')       # 'VOLTage[:DC]', 'CURRent[:DC]', 'RESistance', 'CHARge' (default='VOLT:DC')
# k3.write(':SENS:CURR:APERture <n>') # (default: 60 Hz = 16.67 ms) Set integration rate in seconds: 167e-6 to 200e-3
k3.write(':SENS:CURR:NPLC 1')       # (default = 1) Set integration rate in line cycles (0.01 to 10)
k3.write(':SENS:CURR:RANG:AUTO OFF')# Enable (ON) or disable (OFF) autorange
k3.write(':SENS:CURR:RANG 200e-6')  # Select current range: 0 to 20e-3 (default = 20e-3)
k3.write(':SENS:CURR:REF 0')        # Specify reference: -20e-3 to 20e-3) (default: 0)
k3.write(':SENS:CURR:DIG 6')        # Specify measurement resolution: 4 to 7 (default: 6)

# ---

# Execute configured measurement

k3.write('OUTP ON')         # Turn source ON
k3.write(':INIT')           # Move from IDLE state to ARM Layer 1

time.sleep(5)                 # add delay to watch triggers sequentially unlatch

print("Manually trigger input line to Keithley 6517b via Trigger Link.")

# request readings
data = k3.query_ascii_values(':FETCh?', container=np.array)  # ASCii string in order: READing,TSTamp,CHANnel,VSOurce
# :FETCh? / :DATA:FRESh? / TRACe:DATA? -> get last / new reading / all readings
# data = k3.query_ascii_values(':TRAC:DATA?')  # Read all readings from the buffer
print(data)

# if you want to terminate scan
k3.write(':SOUR:VOLT 0')            # Set voltage level to 0
# k3.write(':ROUT:SCAN:LSEL NONE')    # ROUTe = Command path to control channels; SCAN:LSELect = select scan operation (INTernal, EXTernal, NONE) (default: NONE)

# turn off and close instrument
k3.write(':OUTP OFF')  # turn output off
k3.write('*RST')  # reset GPIB to default
k3.close()

# ---

# clear the TCU and close
TCU.write('C0X')  # clear the present program
time.sleep(0.1)
for i in range(6):
    TCU.write('I{}X'.format(i + 1)) # unlatch all trigger channels
    time.sleep(0.5)                 # add delay to watch triggers sequentially unlatch
TCU.write('2>3')                    # if 2 triggered, trigger out 3
time.sleep(0.1)
TCU.close()