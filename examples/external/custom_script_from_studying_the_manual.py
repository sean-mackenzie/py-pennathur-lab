import pyvisa

"""
1. Connect to Instrument and Configure
"""

GPIB = 23
rm = pyvisa.ResourceManager()
keithley = rm.open_resource("GPIB::{}".format(GPIB))

""" Startup Initialization
*RST
*CLS
*SRE 0
:SYST:BEEP:STAT 0
"""

keithley.write('*RST')
keithley.write('*CLS')
keithley.write('*SRE 0')
keithley.write(':SYST:BEEP:STAT 0')

""" Measurement Setup
:SENS:RES:MODE MAN
:FORMAT:ELEM VOLT, CURR
:SOUR:FUNC VOLT
:SOUR:VOLT:MODE FIX
:SOUR:VOLT:RANG 200
:SOUR:VOLT:LEV -32.7
:SENS:CURR:PROT 1e-3
:SENS:CURR:RANG 10e-6
"""
source_current_range = 105e-6  # Amps
source_voltage_range = 1100  # Volts

source_current_level = 1e-3  # Amps
source_voltage_level = 2200  # Volts

sense_current_protection = 1e-3  # Amps
sense_voltage_protection = 2200  # Volts

sense_current_range = 105e-6  # Amps
sense_voltage_range = 1100  # Volts

# Table 3-5, Section 3-18: Basic source-measure commands

# --- SOURCE COMMANDS
keithley.write('SOURce:FUNCtion[:MODE] VOLT')  # Select source function (name = VOLTage or CURRent).
# keithley.write(':SOUR:FUNC VOLT')
keithley.write(':SOURce:VOLTage:MODE FIXed')  # Select fixed sourcing mode for V-source.
# keithley.write(':SOUR:VOLT:MODE FIX')
keithley.write(':SOURce:CURRent:RANGe ' + str(source_current_range))  # Select I-source range (n = range).
keithley.write(':SOURce:VOLTage:RANGe ' + str(source_voltage_range))  # Select V-source range (n = range).
# keithley.write(':SOUR:VOLT:RANG 200')
keithley.write(':SOURce:CURRent:LEVel ' + str(source_current_level))  # Set I-source amplitude (n = amplitude in amps).
keithley.write(':SOURce:VOLTage:LEVel ' + str(source_voltage_level))  # Set V-source amplitude (n = amplitude in volts).
# keithley.write(':SOUR:VOLT:LEV -32.7')

# --- SENSE COMMANDS
keithley.write(':SENSe:FUNCtion CURRent')  # Select measure function (function = “VOLTage” or “CURRent”).
keithley.write(':SENSe:CURRent:PROTection ' + str(sense_current_protection))  # Set current compliance (n = compliance).
# keithley.write(':SENS:CURR:PROT 1e-3')
keithley.write(':SENSe:VOLTage:PROTection ' + str(sense_voltage_protection))  # Set voltage compliance (n = compliance).
keithley.write(':SENSe:CURRent:RANGe ' + str(sense_current_range))  # Set current measure range (n = range).
# keithley.write(':SENS:CURR:RANG 10e-6')
keithley.write(':SENSe:VOLTage:RANGe ' + str(sense_voltage_range))  # Set voltage measure range (n = range).

# -

# I haven't found out where these go yet
keithley.write(':SENS:RES:MODE MAN')
keithley.write(':FORMAT:ELEM VOLT, CURR')

# -

# keithley.write('')  #

""" Arm Memory
TRIG:SOUR TLINK     (not appropriate for me I think)
TRIG:COUNT 128
TRIG:DELAY 0.015
:OUTP ON
INIT
"""

keithley.write(':OUTPut ON')  # Select output state (state = ON or OFF).


# ----------------------------------------------------------------------------------------------------------------------

"""
10. --- "Source", "Measure", and return to Idle ---

A. --- Idle

A.1 INITiate    [yes, no]


B. --- Arm Layer

B.1 ARM:DIRection   [ACCeptor, SOURce]
    if "ACCeptor":
        proceed to Arm Event Detector
    if "SOURce":
        skip Arm Event Detector

B.2 Arm Event Detector  [ARM:OUTPut, NONE|TENTer Output Trigger]

NOTE: Can also enter B.2 Arm Event Detector via Arm-In Event:
    ARM:SOURce  [IMMediate (GPIB default), BUS, TIMer, MANual, TLINK]


C. --- Trigger Layer

C.1 TRIGger:DIRection   [ACCeptor, SOURce]
    if "ACCeptor":
        proceed to Source Event Detector
    if "SOURce":
        skip Source Event Detector

C.2 Source Event Detector

NOTE: Can also enter C.2 Source Event Detector via Trigger-In Source:
    TRIGger:SOURce  [IMMediate (GPIB default), TLINK]
    TRIGger:INPut   [SOURce (GPIB default)]

C.3 TRIGger:DELay [n_seconds]   (GPIB default: 0.0 seconds)

C.4 SOURCE Action   [TRIGger:OUTPut, SOURce Output Trigger]

C.5 Delay Event Detector

NOTE: Can also enter C.5 Delay Event Detector via Trigger-In Source:
    TRIGger:SOURce  [IMMediate (GPIB default), TLINK]
    TRIGger:INPut   [DELay]

C.6 SOURce:DELay [n_seconds, AUTO]  (GPIB default: 0.001 seconds)
    [TRIGger:OUTPut, DELay Output Trigger]      (GPIB default for TRIGger:OUTPut is NONE)

C.7 Measure Event Detector

NOTE: Can also enter C.7 Measure Event Detector via Trigger-In Source:
    TRIGger:SOURce  [IMMediate (GPIB default), TLINK]
    TRIGger:INPut   [SENSe]

C.8 Measure Action
    [TRIGger:OUTPut, SENSe Output Trigger]      (GPIB default for TRIGger:OUTPut is NONE)

C.9 Another Trigger?    [yes, no]
    [TRIGger:COUNt [n_counts]]      (GPIB default: 1 count)

    if "yes":
        Return to ACCeptor before Source Event Detector
    if "no":
        Return to Arm Layer: [ARM:OUTPut, NONE (GPIB default)|TEXit]

        Another Arm?    [yes, no]
            [ARM:COUNt  [n_counts, INF]]    (GPIB default: 1)
            if "yes":
                Return to Acceptor before Arm Event Detector
            if "no":
                Return to Idle Layer:

                The following commands place the SourceMeter into idle:
                    DCL
                    SDC
                    ABORt
                    *RST
                    SYSTem:PREset
                    *RCL
"""

""" GPIB Defaults
Arm-In Event = Immediate
Trigger-In Source = Immediate
Arm Count = 1
Trigger Count = 1
Trigger Delay = 0.0 seconds
Delay Action = 0.001 seconds
Enabled event detector = Source Event Detector (Delay and Measure detection disabled)
Enabled output triggers = None
Event detection bypasses = Acceptor (both layers)
"""
# 10. --- "Source", "Measure", and return to Idle ---

# A. --- Idle

# A.1 INITiate    [yes, no]
keithley.write(':INITiate')

# B. --- Arm Layer

# B.1 ARM:DIRection   [ACCeptor, SOURce]
#     if "ACCeptor":
#         proceed to Arm Event Detector
#     if "SOURce":
#         skip Arm Event Detector

# B.2 Arm Event Detector  [ARM:OUTPut, NONE|TENTer Output Trigger]
#    TENTer:    enables the triggering on entering the trigger layer
#    TEXit:     enables the trigger on exiting the trigger layer
#    NONE:      disables both triggers                                  (GPIB default)

# NOTE: Can also enter B.2 Arm Event Detector via Arm-In Event:
#     ARM:SOURce  [IMMediate (GPIB default), BUS, TIMer, MANual, TLINK]


# C. --- Trigger Layer

# C.1 TRIGger:DIRection   [ACCeptor, SOURce]
#     if "ACCeptor":
#         proceed to Source Event Detector
#     if "SOURce":
#         skip Source Event Detector


# C.2 Source Event Detector

# NOTE: Can also enter C.2 Source Event Detector via Trigger-In Source:
#     TRIGger:SOURce  [IMMediate (GPIB default), TLINK]
#     TRIGger:INPut   [SOURce (GPIB default)]


# C.3 TRIGger:DELay [n_seconds]   (GPIB default: 0.0 seconds)


# C.4 SOURCE Action   [TRIGger:OUTPut, SOURce Output Trigger]


# C.5 Delay Event Detector

# NOTE: Can also enter C.5 Delay Event Detector via Trigger-In Source:
#     TRIGger:SOURce  [IMMediate (GPIB default), TLINK]
#     TRIGger:INPut   [DELay]


# C.6 SOURce:DELay [n_seconds, AUTO]  (GPIB default: 0.001 seconds)
#     [TRIGger:OUTPut, DELay Output Trigger]      (GPIB default for TRIGger:OUTPut is NONE)


# C.7 Measure Event Detector

# NOTE: Can also enter C.7 Measure Event Detector via Trigger-In Source:
#     TRIGger:SOURce  [IMMediate (GPIB default), TLINK]
#     TRIGger:INPut   [SENSe]


# C.8 Measure Action
#     [TRIGger:OUTPut, SENSe Output Trigger]      (GPIB default for TRIGger:OUTPut is NONE)

keithley.write(':READ?')  # Trigger and acquire reading.


# C.9 Another Trigger?    [yes, no]
#     [TRIGger:COUNt [n_counts]]      (GPIB default: 1 count)

#     if "yes":
#         Return to ACCeptor before Source Event Detector
#     if "no":
#         Return to Arm Layer: [ARM:OUTPut, NONE (GPIB default)|TEXit]

#         Another Arm?    [yes, no]
#             [ARM:COUNt  [n_counts, INF]]    (GPIB default: 1)
#             if "yes":
#                 Return to Acceptor before Arm Event Detector
#             if "no":
#                 Return to Idle Layer:
#
#                 The following commands place the SourceMeter into idle:
#                     DCL, SDC, ABORt, *RST, SYSTem:PREset, *RCL

keithley.write('ABORt')