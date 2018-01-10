import subprocess
import sys
import RPi.GPIO as GPIO
import time
import os
import math
import sys
import json
import datetime
import urllib2
import requests
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
import logging

def setGlobals():
	print "Start setGlobal()"
	global temp
	temp = 6.5
	global Liters
	Liters = 0
	global hum
	hum = 60.45
	global status
	status = False
	global Upstatus
	Upstatus = False
	global water
	water = 20
	global tube 
	tube = 21

def openPin(pin):
	GPIO.output(pin,GPIO.LOW)
	logging.info(str(datetime.datetime.now()) + " Water starts")
	print "openPin()"

def closePin(pin):
	GPIO.output(pin,GPIO.HIGH) 
	logging.info(str(datetime.datetime.now()) + " Water stops")
	print "closePin()"

def setup():
	print "Start setup()"
	#GPIO.setmode(GPIO.BOARD) #Numbers GPIOs by physical location
	GPIO.setup(water, GPIO.OUT) 
	GPIO.setup(tube, GPIO.OUT) 
	GPIO.setup(22,GPIO.IN, pull_up_down=GPIO.PUD_UP)
	closePin(water)
	closePin(tube)
	logging.basicConfig(filename='log.txt',level=logging.DEBUG)			             
		
def getValues(sp):
	print "Start getValues()"
	global Liters,temp,hum
	if sp == 1:
		h = mcp.read_adc(0)
		hum = round((1 - (float(h)/ 1023))* 200 )
		print "Humidity:" + str(hum)
	elif sp == 2:
		t = mcp.read_adc(7)
		if t < 60 and t > 40:
			temp = float(t) - 40
		print "Temperature:" + str(temp)
	elif sp == 3:
		l = "Liters: 0"
		Liters = 0
		print "Running Liters: " + str(Liters)
	logging.debug("Hum" +  str(hum)  + "Temperature:" + str(temp)  + "Running Liters: " + str(Liters))	

# TODO:POst
def getAndWrite():
	print "Start getAndWrite()"
	global hum,temp,Liters,status,data
	for x in range(1, 4):
		getValues(x)
		print "Read value with code: " + str(x)
		if x == 1:
			data = {
						"DataTypeID": 1,
						"NodeID" : 4,
						"Value" : temp,
						"Unit" : "c",
						"Description" : "-"
					}
			req = urllib2.Request('http://jussi.gearhostpreview.com/api/Data')
			req.add_header('Content-Type', 'application/json')
			try:
				response = urllib2.urlopen(req, json.dumps(data))									
			except:
				print "Error getvalues"
		elif x == 2:
			data = {
						"DataTypeID": 2,
						"NodeID" : 4,
						"Value" : hum,
						"Unit" : "%",
						"Description" : "-"
					}
			req = urllib2.Request('http://jussi.gearhostpreview.com/api/Data')
			req.add_header('Content-Type', 'application/json')
			try:
				response = urllib2.urlopen(req, json.dumps(data))									
			except:
				print "Error getvalues"
		elif x == 3:
			data = {
						"DataTypeID": 9,
						"NodeID" : 4,
						"Value" : Liters,
						"Unit" : "l",
						"Description" : "-"
					}
			req = urllib2.Request('http://jussi.gearhostpreview.com/api/Data')
			req.add_header('Content-Type', 'application/json')
			try:
				response = urllib2.urlopen(req, json.dumps(data))									
			except:
				logging.error(str(datetime.datetime.now()) + " request error getvalues")
				print "Error getvalues"

def getStatus():
	print "Start getStatus()"
	global Upstatus, status
	try:
		r = requests.get("http://jussi.gearhostpreview.com/api/Node/4", verify=False, timeout=5)
		response = r.text
		l = json.loads(response)
		Upstatus = l['status']
	except:
		print "getStatus error"
	print str(Upstatus) + " ... Server's status"
	if status == False and Upstatus == True:
		changeStatusTrue()
	elif status == True and Upstatus == False:
		changeStatusFalse()

def changeStatusTrue():
	global status , water
	if status == False:
		status = True
		openPin(water)
		print "Watering... Status: " + str(status)	

def changeStatusFalse():
	global status, water
	if status == True:
		status = False
		closePin(water)
		print "Watering... Status: " + str(status)	
	
if __name__ == '__main__':     # Program start from here
  setGlobals()
 
  CLK = 11
  CS = 8
  MISO = 9
  MOSI = 10
  mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)
  
  setup()
  now = datetime.datetime.now()
  sendDataMorningTime = now.replace(hour=8, minute=0, second=0, microsecond=0)
  sendDataNightTime = now.replace(hour=20, minute=0, second=0, microsecond=0)
  restartTime = now.replace(hour=1, minute=0, second=0, microsecond=0)
  sendDataMorningBit = False
  sendDataNightBit = False

  try:
    while True:
        now = datetime.datetime.now()
<<<<<<< HEAD
        getStatus()          
=======
        getStatus() 
        logging.debug(str(now))
        logging.debug("Status" + str(status))             
>>>>>>> 8683a49cf4506e474340635175bf1a264c21b504
        if sendDataMorningTime < now < sendDataNightTime and sendDataMorningBit == False:
            sendDataMorningBit = True
            getAndWrite()
        elif sendDataNightTime < now and sendDataNightBit == False:
            sendDataNightBit = True
            getAndWrite()
        elif now < restartTime and sendDataMorningBit == True:
            sendDataNightBit = False
            sendDataMorningBit = False		
        time.sleep(2) 	
  except KeyboardInterrupt:
    print "Exiting Safely"
    closePin(water)
    time.sleep(2) 
    GPIO.cleanup() 
