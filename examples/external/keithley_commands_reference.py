# --- GENERAL NOTES ON REMOTE COMMANDS
"""
* Brackets ([ ]) are used to denote optional character sets. These optional characters do not
have to be included in the program message. Do not use brackets in the program message.

* Angle brackets (< >) are used to indicate parameter type. Do not use angle brackets in the program message.

* The Boolean parameter (<b>) is used to enable or disable an instrument operation.
1 or ON enables the operation, and 0 or OFF disables the operation.

* Upper case characters indicate the short-form version for each command word.


# --- SOURCE-MEASURE CAPABILITIES

# NOTE: V-source protection sets the maximum voltage level the SourceMeter can output
k2410_voltage_source_protection = [20, 40, 100, 200, 300, 400, 500, None]  # V (None > 500 V)
# the power-on default is NONE.
# to change, use command:           :SOUR:VOLT:PROT 20

k2410_voltage_ranges = [0.2, 2, 20, 1000]  # V  --> The "range" set the limits for the other functions
k2410_voltage_source_range = [0.21, 2.1, 21, 1100]  # V (correspond to the voltage ranges)
k2410_voltage_measure_range = [0.211, 2.11, 21.1, 1100]  # V (correspond to the voltage ranges)
k2410_voltage_compliance_range = [0.21, 2.1, 21, 1100]  # V (correspond to the voltage ranges)
# NOTE: "compliance" is equivalent to "protection"

k2410_current_range = [1, 10, 100, 1000, 20000]  # micro Amps
k2410_current_source_range = [1.05, 10.5, 105, 1050, 21000]  # micro Amps (correspond to the current ranges)
k2410_current_measure_range = [1.055, 10.55, 105.5, 1055, 21100]  # micro Amps (correspond to the current ranges)
k2410_current_compliance_range = [1.05, 10.5, 105, 1050, 21000]  # micro Amps (correspond to the current ranges)
# NOTE: "compliance" is equivalent to "protection"

k2410_max_power = 22  # Watts

"""

# --- A NOTE ON !!! SPEED !!!
"""
* For fastest response to commands, always use short forms.Program messages

* For fastest operation, eliminate the first colon from commands    (Example:   :stat:pres = stat:pres)

* For fastest operation, do not send optional data                  (Example:   FORM:ELEM:SENS? = FORM:ELEM?)

"""

# --- FORMat
"""
:FORMat
    :SREGister <name>           Select data format for reading status event registers       (default = ASCii)
    [:DATA] <type>[<,length>]   Specify data format (ASCii, REAL, 32, or SREal).            (default = ASCii)
    [:DATA]?                    Query data format
    :ELEMents
        [:SENSe[1]] <item list> Specify data elements (VOLTage, CURRent, RESistance, TIME)  (default = All)
        [:SENSe[1]]?            Query data format elements 
"""

# --- OUTPut
"""
:OUTPut[1]
    :STATe <b>                  Turn source on or off.                                      (default = OFF)
    :STATe?                     Query state of source. 
    :SMODe <name>               Select output off mode (HIMPedance, NORMal, ZERO, GUARd)    (default = GUARd for 2410)
"""

# --- ROUTe
"""
:ROUTe
    :TERMinals <name>           Select in/out terminals: (FRONt or REAR)                    (default = FRONt)
    :TERMinals?                 Query in/out terminals. 
"""

# --- SENSe
"""
[:SENSe[1]]
    :DATA
        [:LATest?]              Return only the most recent reading.
    :FUNCtion
        :CONCurrent <b>         Enable or disable ability to more more than one function simult.    (default = ON)
        :CONCurrent?            Query concurrent state. 
        [:ON] <function list>   Specificy functions to enable (VOLTage[:DC], CURRent[:DC], or RESistance)   (def = CURR)
    :CURRent[:DC]
        :RANGe
            :AUTO <b>           Enable or disable auto range                                (default = ON)
        :NPLCycles <n>          Specify integration rate (in line cycles): 0.01 to 10e3     (default = 1.0)
        :NPLCycles?             Query integration rate.
        :PROTection             
            [:LEVel] <n>        Specify current limit for V-source                          (default = 105 micro Amps)
            [:LEVel]?           Query current compliance limit.
    :VOLTage[:DC]
        all of the same functions for :CURR
        :PROTection
            [:LEVel] <n>        Specify voltage limit for I-source                          (default = 21 V)
"""


# --- SOURce
"""
[:SOURce[1]]
    :FUNCtion
        [:MODE] <name>          Select source mode (VOLTage, CURRent)                       (default = VOLTage)
    :DELay <n>                  Specify settling time (in seconds): 0.0 to 9999             (default = 0)
        :AUTO <b>               Enable or disable auto settling time                        (default = ON)
        :AUTO?                  Query state of auto settling time.
    :CURRent
        all of the same functions as :VOLTage
    :VOLTage
        :MODE <n>               Select V-source mode (FIXed, SWEep, or LIST)                (default = FIXed)
        :MODE?                  Query V-source mode
        :RANGe <n>|UP|DOWN      Select fixed V-source range                                 (default = 21 V)
            :AUTO <b>           Enabel or disable autoranging                               (default = ON)
        [:LEVel]
            [:IMMediate]        Set specified level immediately
                [:AMPLitude] <n>    Specify voltage level                                   (default = 0 V)
                

"""

# ---
"""


"""


# ---
"""


"""

# ---
"""


"""