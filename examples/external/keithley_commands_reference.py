# --- GENERAL NOTES ON REMOTE COMMANDS
"""
* Brackets ([ ]) are used to denote optional character sets. These optional characters do not
have to be included in the program message. Do not use brackets in the program message.

* Angle brackets (< >) are used to indicate parameter type. Do not use angle brackets in the program message.

* The Boolean parameter (<b>) is used to enable or disable an instrument operation.
1 or ON enables the operation, and 0 or OFF disables the operation.

* Upper case characters indicate the short-form version for each command word.

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