# -*- coding: utf-8 -*-
"""
Keithley I-V Sweep
Demis John, 2018-10-12

Program to sweep voltage & measure current on Keithley SMU
Known bugs: the plot window opens *behind* the current window.
Also, file is saved *usually* in same directory as this script - but at one point it kept saving into the PythonXY directory, which was confusing.  Probably need to set the Python working directory to be sure.  Use `import os; os.getcwd()` to see where it will save.

Edit/Run this file via Spyder / Anaconda Python
Installed PyVISA for communication.
Updated for Python 3.x


Based off Steve Nichols' Script from ~2010
"""

##########################################
##########################################
''' User Settings:     '''

SaveFiles = True   # Save the plot & data?
DevName = 'w25 - Au on thermal SiO2' #in filename of  saved plot 

NewFolder = True    # save data into a subfolder?
FolderName = 'data'    # Only used if NewFolder=True

Keithley_GPIB_Addr = 23     # GPIB Address of the Keithley (in Menu/Comms)

'''Voltage Sweep settings'''
CurrentCompliance = 1.00e-3    # compliance (max) current, in Amps
intV = 0       # start and end voltage
minV = -150      # min voltage
maxV = 150      # max voltage
numpoints = 50   # number of points in sweep
dir = 'pos'      # initial sweep direction: 'pos'itive or 'neg'ative.

##########################################
##########################################


''' You shouldn't need to edit anything below'''
## Import some modules:
import pyvisa as visa             # PyVISA module for GPIB communication, installed
import time             # to allow pause between measurements
import os               # manipulate file paths and make directories
import numpy as np      # matlab-like array math

#from pylab import *    # for matlab-style plotting commands like `plot(x,y)`
import matplotlib.pyplot as plt # for python-style plottting, like 'ax1.plot(x,y)'


# organize Voltage array into sequence
minVdesc = np.linspace(intV,minV,numpoints)
minVasc  = minVdesc[::-1]
maxVasc  = np.linspace(intV, maxV, numpoints)
maxVdesc = maxVasc[::-1]

if dir == 'pos':
    Vspace   = np.concatenate((maxVasc,maxVdesc,minVdesc,minVasc), axis=0)
elif dir == 'neg':
    Vspace   = np.concatenate((minVdesc,minVasc,maxVasc,maxVdesc), axis=0)
#if intV != 0:
#    initVsweep = np.linspace(0,intV,numpoints)
#    Vspace = np.concatenate((initVsweep, Vspace), axis=0)


# Open Visa connections to instruments
#keithley = visa.GpibInstrument(22)     # GPIB addr 22
rm = visa.ResourceManager()
keithley = rm.open_resource(  'GPIB::' + str(Keithley_GPIB_Addr)  )


# Setup Keithley for  current loop

# Setup electrodes that are voltage
keithley.write("*RST")
#print("reset the instrument")
time.sleep(0.5)    # add second between
keithley.write(":SOUR:FUNC:MODE VOLT")
keithley.write(":SENS:CURR:PROT:LEV " + str(CurrentCompliance))
keithley.write(":SENS:CURR:RANGE:AUTO 1")   # set current reading range to auto (boolean)
keithley.write(":OUTP ON")                    # Output on    

Voltage=[]
Current = []
for V in Vspace:
    #Voltage.append(V)
    print("Voltage set to: " + str(V) + " V" )
    keithley.write(":SOUR:VOLT " + str(V))
    time.sleep(0.1)    # add second between
    data = keithley.write(":READ?")   #returns string with many values (V, I, ...)
    if isinstance(data, (str)):
        answer = data.split(',')    # remove delimiters, return values into list elements
        I = eval(answer.pop(1)) * 1e6  # convert to number
    else:
        answer = data
        I = float(answer) * 1e6

    print(data)
    print(I)

    Current.append( I )
    
    # vread = eval( answer.pop(0) )
    vread = V
    Voltage.append(vread)
    #Current.append(  I  )          # read the current
    
    print("--> Current = " + str(Current[-1]) + ' uA')   # print last read value
#end for(V)
keithley.write(":OUTP OFF")

#set to current source, voltage meas
keithley.write(":SOUR:FUNC:MODE curr")
keithley.write(":SOUR:CURR " + str(CurrentCompliance))
keithley.write(":SENS:volt:PROT:LEV " + str(max(Voltage))  )
keithley.write(":SENS:volt:RANGE:AUTO 1")

keithley.write("SYSTEM:KEY 23") # go to local control
keithley.close()
    
###### Plot #####
    
fig1, ax1 = plt.subplots(nrows=1, ncols=1)         # new figure & axis

line1 = ax1.plot(Voltage[0:numpoints], Current[0:numpoints], 'b+-', label='ascending #1')
line1 = ax1.plot(Voltage[numpoints-1:numpoints*2], Current[numpoints-1:numpoints*2],'.-',color='lightskyblue', label='descending #1')
line1 = ax1.plot(Voltage[numpoints*2-1:numpoints*3], Current[numpoints*2-1:numpoints*3], 'r.-', label='ascending #2')
line1 = ax1.plot(Voltage[numpoints*3-1:], Current[numpoints*3-1:], '+-', color='lightcoral', label='descending #2')

ax1.set_xlabel('Voltage (V)')
ax1.set_ylabel('Current (uA)')
ax1.set_title('I-V Curve - ' + DevName)

ax1.grid(True)
plt.legend()

fig1.show()  # draw & show the plot - unfortunately it often opens underneath other windows


if SaveFiles:
    curtime = time.strftime('%Y-%m-%d_%H%M.%S')
    SavePath = 'I-V Curve - ' + DevName + ' - [' + curtime +']'
    # create subfolder if needed:
    if NewFolder and not os.path.isdir(FolderName): os.mkdir(FolderName)
    if NewFolder: SavePath = os.path.join(FolderName, SavePath )
    fig1.savefig(  SavePath + '.png'  )
    
    data = np.array(  list( zip(Current, Voltage) )  )
    np.savetxt( SavePath + '.txt', data, fmt="%e", delimiter="\t", header="Current (mA)\tVoltage (V)" )
    print("Saved data to:\n    %s" %(os.path.abspath(SavePath))  )
    #np.array(Voltage).tofile(  os.path.join(DevName, 'I-V Voltage - ' + DevName + ' - [' + curtime +'].txt' )  )
    #np.array(Current).tofile(  os.path.join(DevName, 'I-V Current - ' + DevName + ' - [' + curtime +'].txt' )  )
#end if(SaveFiles)


#attempt to force figure to front:
fig1.canvas.window().raise_()