#!/usr/bin/env python -w
# -*- coding: UTF-8 -*-

import os
import os.path
import re
import time
import thread
import threading
import serial
import sys
import datetime
import zmq
import Queue

def mean(data):
   return sum(data)/float(len(data))

def stabw(data, mittelwert = None):
   if mittelwert == None:
      mw = mean(data)
   else:
      mw = mittelwert
   sumA = 0.0
   for i in data:
      sumA += (mw-i)**2
   return sqrt(sumA/(len(data)-1))


# Vergleichsfunktion für eine Sortierroutine. Das ist ein Schnipsel aus dem Internet.
def lcmp(idx):
    def t(i, j):
        if i[idx] < j[idx]:        # kleiner
            return -1
        elif i[idx] > j[idx]:      # größer
            return 1
        else:                      # gleich
            return 0
    return t

# Transpose a list containing lists
# from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/410687
def transposed(lists):
   if not lists: return []
   return map(lambda *row: list(row), *lists)

# Transposed means
def transposedAndMeaned(dataArr):
   transpDataArr = transposed(dataArr)
   meanArr = []
   for pixelArr in transpDataArr:
      meanArr.append(mean(pixelArr))
   return meanArr
                      
class VT200:
        def __init__(self, port = None, logFileName = None):
                self.port = port
                self.logFileName = logFileName
                self.lastWriteTime = None
                # $GPGGA,072718.000,0734.0556,S,11252.5378,E,2,9,0.86,19.4,M,11.6,M,0000,0000*7E
                # $GPGGA,081242.042,5324.3086,N,01025.6195,E,0,0,,103.9,M,46.1,M,,*40
                self.reGPGGA = re.compile(".*\$(GPGGA,([0-9]*\.?[0-9]+),([0-9]*\.?[0-9]+),(.),([0-9]*\.?[0-9]+),(.),(\d),(\d*),([0-9]*\.?[0-9]+)?,([0-9]*\.?[0-9]+)?,(.),([0-9]*\.?[0-9]+),(.),\d*,\d*)([\*[0-9A-Fa-f]+)?")
                # $GPRMC,072717.000,A,0734.0556,S,11252.5378,E,0.00,126.37,241010,,,D*7F
                self.reGPRMC = re.compile("(.*)\$GPRMC,([0-9]*\.?[0-9]+),(.),([0-9]*\.?[0-9]+),(.),([0-9]*\.?[0-9]+),(.),([0-9]*\.?[0-9]+),([0-9]*\.?[0-9]+),([0-9]*\.?[0-9]+),([0-9]*\.?[0-9]+)?,(.)?,(.)([\*[0-9A-Fa-f]+)?")
                #self.reGPRMCinclTime = re.compile("(\d\d\.\d\d.\d\d\d\d\s*\d\d:\d\d:\d\d)\s*\$GPRMC,([0-9]*\.?[0-9]+),(.),([0-9]*\.?[0-9]+),(.),([0-9]*\.?[0-9]+),(.),([0-9]*\.?[0-9]+),([0-9]*\.?[0-9]+),([0-9]*\.?[0-9]+),([0-9]*\.?[0-9]+)?,(.)?,(.)([\*[0-9A-Fa-f]+)?")
                
                self.lastGPGGAtime = None
                self.lastGPRMCtime = None
                self.lastGPGGAtimepoint = None
                
                self.hdop            = None
                self.height          = None
                self.heightUnit      = None
                self.heightGmE       = None
                self.heightGmEUnit   = None
                self.noOfSatellites = None
        
        def interpretString(self, strA = None):
                # Den GRrMC - Datensatz verwende ich für Datum, Uhrzeit, Position, Geschwindigkeit und Richtung der Bewegung
                # den GPGGA - Datensatz dann für die Qualität der Messung, die Höhe über dem Geoid usw.
                                                        
                if strA == None:
                        if self.port <> None:
                                strA = self.waitForAnswer()
                        else:
                                return None
                
                mtchGPGGA = self.reGPGGA.match(strA)
                mtchGPRMC = self.reGPRMC.match(strA)
                if mtchGPGGA:
                        self.lastGPGGAtimepoint = time.time()
                        t = mtchGPGGA.group(2)
                        self.lastGPGGAtime = {'hour' : int(t[0:2],10), 'minutes' : int(t[2:4],10), 'seconds' : float(t[4:])}
                        #print self.lastGPGGAtime
                        #print "2\t" + mtchGPGGA.group(2)# Time HHMMSS.sssss
                        #print "3\t" + mtchGPGGA.group(3)# Latitude
                        #print "4\t" + mtchGPGGA.group(4)# N/S [+/-]
                        #print "5\t" + mtchGPGGA.group(5)# Longitude
                        #print "6\t" + mtchGPGGA.group(6)# E/W [+/-]
                        
                        #print "7\t" + mtchGPGGA.group(7)# Quality of Measurement
                        #print "8\t" + mtchGPGGA.group(8)# Number of Sattelites
                        #print "9\t" + mtchGPGGA.group(9)# horizontal dilution of precision (HDOP)
                        #print "10\t" + mtchGPGGA.group(10)# height above geoid
                        #print "11\t" + mtchGPGGA.group(11)# unit of height
                        #print "12\t" + mtchGPGGA.group(12)# height geoid minus height ellipsoid
                        #print "13\t" + mtchGPGGA.group(13)# unit of height
                        #print "14\t" + mtchGPGGA.group(14)# checksum
                        if mtchGPGGA.group(9) <> None:
                                self.hdop = float(mtchGPGGA.group(9))
                        else:
                                self.hdop = None
                        
                        self.height = float(mtchGPGGA.group(10))
                        self.heightUnit = mtchGPGGA.group(11)
                        self.heightGmE = float(mtchGPGGA.group(12))
                        self.heightGmEUnit = mtchGPGGA.group(13)
                        
                        self.noOfSatellites = int(mtchGPGGA.group(8))
                        
                        return None
                elif mtchGPRMC:
                        #print mtchGPRMC.group(0)
                        timestr = mtchGPRMC.group(2)
                        datestr = mtchGPRMC.group(10)
                        if self.port <> None:
                                sysTime = datetime.datetime.fromtimestamp(time.time())
                        else:
                                sysTime = datetime.datetime.strptime(mtchGPRMC.group(1), "%d.%m.%Y %H:%M:%S")
                        #print mtchGPRMC.group(0)
                        #print mtchGPRMC.group(1)
                        #print sysTime
                        #print sysTime.second
                        self.lastGPRMCtime = datetime.datetime.strptime(timestr[0:6] + " " + datestr, "%H%M%S %d%m%y")
                        #print self.lastGPRMCtime
                        
                        latitude = int(mtchGPRMC.group(4)[0:2],10) + float(mtchGPRMC.group(4)[2:]) / 60.0
                        if mtchGPRMC.group(5) == "N":
                                pass
                        elif mtchGPRMC.group(5) == "S":
                                latitude = latitude * (-1)
                        else:
                                print "Unknown latitude character : '%s'! Exiting ..." % (mtchGPRMC.group(5))
                        #print "latitude: %3.9f" % (latitude)
                        
                        longitude = int(mtchGPRMC.group(6)[0:3],10) + float(mtchGPRMC.group(6)[3:]) / 60.0
                        if mtchGPRMC.group(7) == "E":
                                pass
                        elif mtchGPRMC.group(7) == "W":
                                longitude = longitude * (-1)
                        else:
                                print "Unknown latitude character : '%s'! Exiting ..." % (mtchGPRMC.group(7))
                        #print "longitude: %3.9f" % (longitude)
                        
                        speed = float(mtchGPRMC.group(8))
                        #print "Speed: %.3f" % (speed)
                        
                        direction = float(mtchGPRMC.group(9))
                        #print "Direction: %.2f" % (direction)
                        
                        if (self.lastGPGGAtimepoint == None) or ((time.time() - self.lastGPGGAtimepoint) > 3):
                               return (latitude, longitude)
                               # return (sysTime, self.lastGPRMCtime, latitude, longitude, speed, direction, None, \
                                       # None, None, None, None, None)
                        else:
                                #return (sysTime, self.lastGPRMCtime, latitude, longitude, speed, direction, self.height, \
                                        #self.heightUnit, self.heightGmE, self.heightGmEUnit, self.hdop, self.noOfSatellites)
                                return (latitude, longitude)
                                
                        #print "1\t" + mtchGPRMC.group(2)# Time
                        #print "2\t" + mtchGPRMC.group(3)# Status
                        #print "3\t" + mtchGPRMC.group(4)# Latitude
                        #print "4\t" + mtchGPRMC.group(5)# N/S [+/-]
                        #print "5\t" + mtchGPRMC.group(6)# Longitude
                        #print "6\t" + mtchGPRMC.group(7)# E/W [+/-]
                        #print "7\t" + mtchGPRMC.group(8)# Speed (knots)
                        #print "8\t" + mtchGPRMC.group(9)# direction of movement
                        #print "9\t" + mtchGPRMC.group(10)# Date
                        
                        #return mtchGPRMC
                else:
                        #print "No match"
                        return None

        def waitForAnswer(self):
                retString = ""
                lastCharT = time.time()
                while (time.time() - lastCharT) < 1.0:
                    buchst = self.port.read()
                    if buchst == '\n':
                            #print retString
                            break
                    if len(buchst) > 0:
                        lastCharT = time.time()
                        retString += buchst
                        
                    
                    if len(retString) > 100:
                            sys.exit()
                if self.logFileName <> None:
                        f = open(self.logFileName, 'a')
                        f.write(retString + "\n")
                        f.close()
                return retString


if __name__ == '__main__': 

        serIN = serial.Serial('COM4', 4800, timeout=0.0001,
                              bytesize=serial.EIGHTBITS,
                              parity=serial.PARITY_NONE,
                              stopbits=serial.STOPBITS_ONE)
        serIN.flushInput()
        vt = VT200(serIN)
        #temp_list = []
        #temp_list.append(vt.interpretString())
        #if (str(temp_list[0]) is None):
         #   print temp_list[0]
        
        while 1:
                #print "kkk"
                context = zmq.Context()
                sock = context.socket(zmq.REQ)
                sock.connect("tcp://127.0.0.1:5677")
                #if(vt.interpretString() != "none"):sock.send(" ".join(str(vt.interpretString())))
                #if(vt.interpretString() != "None"):
                #var1 = str(vt.interpretString(2))
                #print var1
                temp_list = []
                temp_list.append(vt.interpretString())
                if temp_list[0] is not None:
                    sock.send("".join(str(temp_list[0])))
                    print str(temp_list[0])               
                
        sock.close()
        context.term()
        vt = VT200()

       # print vt.interpretString("$GPGGA,072718.000,0734.0556,S,11252.5378,E,2,9,0.86,19.4,M,11.6,M,0000,0000*7E")
        #print vt.interpretString("$GPRMC,072717.000,A,0734.0556,S,11252.5378,E,0.00,126.37,241010,,,D*7F")

        dataDir = "/home/carsten/Desktop/2010-10-24/DeviceData/gps-carsten"
        fList = os.listdir(dataDir)
        fList.sort()
        
        tmpLst = []
        
        outfile = open(dataDir + "-results.csv", 'w')
        outfile.write("Time;GPStime;latitude;longitude;speed;direction;height;heightUnit;heightGeoidMinusEllipsoid;heightGeoidMinusEllipsoidUnit;hdop;noOfSatellites\r\n")
        
        for fName in fList:
                
                fA = open(os.path.join(dataDir, fName))
                for i in fA:
                        res = vt.interpretString(i)
                        if res <> None:
                                
                                timeA = None
                                tDiff = None
                                
                                if   (res[0].second > 55) or (res[0].second < 5):
                                        #print res[0].second
                                        #print res
                                        tmpLst.append(res)
                                        
                                elif len(tmpLst) > 0:
                                        # Time which is used by the FB
                                        #print tmpLst[0]
                                        t = tmpLst[0][0]
                                        #print "xx -- " + str(t)
                                        timeA = datetime.datetime(t.year, t.month, t.day, t.hour, t.minute) + datetime.timedelta(minutes=int(round(t.second/60.0)))
                                        #print timeA
                                        del(t)
                                        
                                        # Time difference between GPS and FB
                                        tDiff = tmpLst[0][1] - tmpLst[0][0]
                                        #print tDiff

                                        if len(tmpLst) > 1:
                                                
                                                tmp2 = transposed(tmpLst)
                                                # noOfSatellites is nor the the last row
                                                #print "----------------------" 
                                                tmp3 = []
                                                for i in tmpLst:
                                                        if i[-1] == max(tmp2[-1]):
                                                                tmp3.append(i)                                          
                                                tmp2 = transposed(tmp3)
                                                
                                                tmp3 = [timeA, timeA + tDiff]
                                                
                                                # latitude
                                                tmp3.append(mean(tmp2[2]))
                                                # longitude
                                                tmp3.append(mean(tmp2[3]))
                                                # speed
                                                tmp3.append(mean(tmp2[4]))
                                                # direction
                                                tmp3.append(mean(tmp2[5]))
                                                # height
                                                tmp3.append(mean(tmp2[6]))
                                                # heightUnit
                                                tmp3.append(tmp2[7][0])
                                                
                                                # heightGmE
                                                tmp3.append(mean(tmp2[8]))
                                                # heightGmEUnit
                                                tmp3.append(tmp2[9][0])
                                                # hdop
                                                tmp3.append(mean(tmp2[10]))
                                                # noOfSatellites
                                                tmp3.append(tmp2[11][0])                                                
                                                del(tmp2)
                                                tmpLst = []
                                                
                                                strA = str(tmp3.pop(0))
                                                for i in tmp3:
                                                        strA += ";" + str(i)
                                                strA += "\r\n"
                                                outfile.write(strA)
                                        else:
                                                tmp3 = [timeA, timeA + tDiff]
                                                # latitude
                                                tmp3.append(tmpLst[0][2])
                                                # longitude
                                                tmp3.append(tmpLst[0][3])
                                                # speed
                                                tmp3.append(tmpLst[0][4])
                                                # direction
                                                tmp3.append(tmpLst[0][5])
                                                # height
                                                tmp3.append(tmpLst[0][6])
                                                # heightUnit
                                                tmp3.append(tmpLst[0][7])
                                                
                                                # heightGmE
                                                tmp3.append(tmpLst[0][8])
                                                # heightGmEUnit
                                                tmp3.append(tmpLst[0][9])
                                                # hdop
                                                tmp3.append(tmpLst[0][10])
                                                # noOfSatellites
                                                tmp3.append(tmpLst[0][11])

                                                tmpLst = []
                                        
                                                strA = str(tmp3.pop(0))
                                                for i in tmp3:
                                                        strA += ";" + str(i)
                                                strA += "\r\n"
                                                outfile.write(strA)
                                
                                #time.sleep(.02)
                                



# aus http://www.kowoma.de/gps/zusatzerklaerungen/NMEA.htm
#$GPGGA,191410,4735.5634,N,00739.3538,E,1,04,4.4,351.5,M,48.0,M,,*45
       #^      ^           ^            ^ ^  ^   ^       ^     
       #|      |           |            | |  |   |       |    
       #|      |           |            | |  |   |       Höhe Geoid minus
       #|      |           |            | |  |   |       Höhe Ellipsoid (WGS84)
       #|      |           |            | |  |   |       in Metern (48.0,M)
       #|      |           |            | |  |   |
       #|      |           |            | |  |   Höhe über Meer (über Geoid)
       #|      |           |            | |  |   in Metern (351.5,M)
       #|      |           |            | |  |
       #|      |           |            | |  HDOP (horizontal dilution
       #|      |           |            | |  of precision) Genauigkeit
       #|      |           |            | |
       #|      |           |            | Anzahl der erfassten Satelliten
       #|      |           |            |
       #|      |           |            Qualität der Messung
       #|      |           |            (0 = ungültig)
       #|      |           |            (1 = GPS)
       #|      |           |            (2 = DGPS)
       #|      |           |            (6 = geschätzt nur NMEA-0183 2.3)
       #|      |           |
       #|      |           Längengrad
       #|      |
       #|      Breitengrad
       #|
       #Uhrzeit
