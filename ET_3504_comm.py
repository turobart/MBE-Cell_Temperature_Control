#!/usr/bin/python3
# -*- coding: utf-8 -*-
import serial
import time
import math

def getCOMports():
    ports = ['COM%s' % (i + 1) for i in range(256)]
    com_ports = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            com_ports.append(port)
        except (OSError, serial.SerialException):
            pass
    del ports
    return com_ports


def connectET(currentCOM):
    global eurothermSerial
    eurothermSerial = serial.Serial(currentCOM, 9600, serial.SEVENBITS, serial.PARITY_EVEN, 1)
    
def disconnectET():
    global eurothermSerial
    eurothermSerial.close()


def initCommunication():
    global eurothermSerial
    GID='0'
    cellsStatus = []
    for UID in range(1,7):
        UID=str(UID)
        GetTempCommand=bytes([4, ord(GID), ord(GID), ord(UID), ord(UID), ord('P'), ord('V'), 5])
        eurothermSerial.write(GetTempCommand)
        time.sleep(0.1)
        bytesToRead = eurothermSerial.inWaiting()
        if bytesToRead:
            result=eurothermSerial.read(bytesToRead)
            cellsStatus.append(str(result[3:-3].decode()))
        else:
            cellsStatus.append('NC')
    return cellsStatus


def convertNumberForEurotherm(numberToCovert):
    numberToCovert=int(numberToCovert)
    hundrets=math.floor(numberToCovert/100)
    tens=math.floor((numberToCovert-hundrets*100)/10)
    units=numberToCovert-hundrets*100-tens*10
    return str(hundrets), str(tens), str(units)

def XOR_command(toXOR):
    temp_xor=0
    for i in range(len(toXOR)):
        temp_xor^=toXOR[i]
    return temp_xor

    
# def setTemp(temperature, *args):
#     rampGiven=False
#     if isinstance(args[0], int):
#         rampGiven = True
#         ramp = args[0]
#         if (ramp<0 or ramp >100) and rampGiven:
#             raise ValueError('Wrong ramp. Choose in 0-100 °C/m range.')
# 
#     if temperature<0 or temperature>2000:
#         raise ValueError('Wrong temperature. Choose in 0-2000 °C range.')
#     if rampGiven:
#         for arg in args[1:]:
#             arg.targetSP_value.setText(str(temperature))
#             arg.ramp_value.setText(str(ramp))
#             arg.cellButton.setChecked(True)
# #             try:
#             temperatureSet, rampSet = setCellParameters(int(temperature), int(ramp), '0', arg.cellID)
# #             except Exception as e:
# #                 print(e)
#     else:
#         for arg in args:
#             arg.targetSP_value.setText(str(temperature))
#             arg.cellButton.setChecked(True)
#     return 'ddd'
#     linkToGui.parent.parent().dataConsole.consoleEdit.setPlainText('Done')
            
def getTemp(GID, UID):
    global eurothermSerial
    Tresult = 'er'
    SPresult = 'er'
    C1='P' #first character of the parameter being accessed
    C2='V' #second character of the parameter being accessed
    GetTempCommand=bytes([4, ord(GID), ord(GID), ord(UID), ord(UID), ord(C1), ord(C2), 5])
    GetSPCommand=bytes([4, ord(GID), ord(GID), ord(UID), ord(UID), ord('S'), ord('P'), 5])
#     GetSPCommand=bytes([15])
#     print(GetSPCommand)
    eurothermSerial.write(GetTempCommand)
    time.sleep(0.06)
    
    bytesToRead = eurothermSerial.inWaiting()
    if bytesToRead:
        Tresult=eurothermSerial.read(bytesToRead)
    
    
    eurothermSerial.write(GetSPCommand)
    time.sleep(0.06)
    
    bytesToRead = eurothermSerial.inWaiting()
    if bytesToRead:
        SPresult=eurothermSerial.read(bytesToRead)
#     print(SPresult)
#     if SPresult[-1] == XOR_command(SPresult[1:-1]):
#         print( str(SPresult[3:-3].decode()))
    if Tresult[-1] == XOR_command(Tresult[1:-1]):
        return str(Tresult[3:-3].decode()), str(SPresult[3:-3].decode())
    else:
        return str(Tresult), str(SPresult)
#         if (int(result[3:-3].decode())-5) >= int(SPresult[3:-3].decode()):
#             print(False)
#             return str(result[3:-3].decode()), False
#         else:
#             print(True)
#             return str(result[3:-3].decode()), True
    
    
def setCellParameters(tempToSet, rampToSet, GID, UID):
    global eurothermSerial
    C1='S' #first character of the parameter being accessed
    C2='L' #second character of the parameter being accessed
    
    tempHundrets, tempTens, tempUnits = convertNumberForEurotherm(tempToSet)
    tempCommand=bytes([ord(C1), ord(C2), ord(tempHundrets), ord(tempTens), ord(tempUnits),  3])
    XORedTempCommand=XOR_command(tempCommand)
    setTempCommand=bytes([4, ord(GID), ord(GID), ord(UID), ord(UID), 2])+tempCommand+bytes([XORedTempCommand])
    
    rampleHundrets, rampTens, rampUnits = convertNumberForEurotherm(rampToSet)
    rampCommand=bytes([ord('R'), ord('R'), ord(rampleHundrets), ord(rampTens), ord(rampUnits),  3])
    XORedRampCommand=XOR_command(rampCommand)
    setRampCommand=bytes([4, ord(GID), ord(GID), ord(UID), ord(UID), 2])+rampCommand+bytes([XORedRampCommand])
    
    eurothermSerial.write(setTempCommand)
    time.sleep(0.06)
    bytesToRead = eurothermSerial.inWaiting()
    result=eurothermSerial.read(bytesToRead)
#     print(result)
    if int.from_bytes(result, byteorder='big') == 6:
        temperatureSet = True
    else:
        temperatureSet = False
#     print(int.from_bytes(result, byteorder='big'))
        
    eurothermSerial.write(setRampCommand)
    time.sleep(0.06)
    bytesToRead = eurothermSerial.inWaiting()
    result=eurothermSerial.read(bytesToRead)
    if int.from_bytes(result, byteorder='big') == 6:
        rampSet = True
    else:
        rampSet = False
    return temperatureSet, rampSet
        