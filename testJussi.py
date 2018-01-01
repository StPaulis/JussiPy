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
from sht_sensor import Sht
# from pi_sht1x import SHT1x

GPIO.setwarnings(False)

def setGlobals():
	print ("Start setGlobal()")
	global temp
	temp = 25.32
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
	global pouring,lastPinState,pinState,lastPinChange,pinChange
	global pinDelta,hertz,flow,litersPoured,pintsPoured
	pouring = False
	lastPinState = False
	pinState = 0
	lastPinChange = int(time.time() * 1000)
	pourStart = 0
	pinChange = lastPinChange
	pinDelta = 0
	hertz = 0
	flow = 0
	litersPoured = 0
	pintsPoured = 0
	global now

def openPin(pin):
	GPIO.output(pin,GPIO.LOW)
	print ("openPin()")

def closePin(pin):
	GPIO.output(pin,GPIO.HIGH) 
	logging.debug("closePin()")

def setup():
	logging.debug("Start setup()")
	global sht,water,tube
	sht = Sht(27, 17)
	GPIO.setup(water, GPIO.OUT) 
	GPIO.setup(tube, GPIO.OUT) 
	GPIO.setup(22,GPIO.IN, pull_up_down=GPIO.PUD_UP)
	closePin(water)
	closePin(tube)
	logging.basicConfig(filename='log.txt',level=logging.DEBUG)		             
		
def getValues(sp):
	logging.debug("Start getValues()")
	global Liters,temp,hum,now,litersPoured
	if sp == 1:
		h = mcp.read_adc(0)
		hum = (1 - (float(h)/ 1023))* 200 
		logging.debug("Humidity:" + str(hum))
	elif sp == 2:
		t = mcp.read_adc(1)
		temp = float(t) - 40
		logging.debug("Temperature:" + str(temp))
	elif sp == 3:
		l = ("Liters: 0")
		Liters = litersPoured
		print ("Running Liters: " + str(Liters))
		logging.debug("Running Liters: " + str(Liters))

def getValuesDigital(sp):
	print ("getValuesDigital()")
	global Liters,temp,hum,sht
	if sp < 3:
		temp = sht.read_t()
		hum = sht.read_rh(t)
		dew_point = sht.read_dew_point(t, rh)
		print ("Humidity:" + str(hum) + ", Temp:" + str(temp))
		logging.debug("Humidity:" + str(hum) + ", Temp:" + str(temp))
	elif sp == 3:
		l = ("Liters: 0")
		Liters = 0
		print ("Running Liters: " + str(Liters))
		logging.debug("Running Liters: " + str(Liters))		

# TODO:POst
def getAndWrite():
	print ("Start getAndWrite()")
	global hum,temp,Liters,status,data
	for x in range(1, 4):
		getValues(x)
		#getValuesDigital(x)
		print ("Read value with code: " + str(x))
		time.sleep(2) 
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
				print ("Response :" + str(response))								
			except:
				print ("Error getvalues")

def getStatus():
	print ("Start getStatus()")
	global Upstatus, status
	try:
		r = requests.get("http://jussi.gearhostpreview.com/api/Node/4", verify=False, timeout=5)
		response = r.text
		l = json.loads(response)
		Upstatus = l['status']
	except:
		logging.error("getStatus error")
	logging.info(str(Upstatus) + " ... Server's status")
	if status == False and Upstatus == True:
		changeStatusTrue()
	elif status == True and Upstatus == False:
		changeStatusFalse()

def changeStatusTrue():
	global status , water
	if status == False:
		status = True
		openPin(water)
		print ("Watering... Status: " + str(status))	
		logging.debug("Watering... Status: " + str(status))	

def changeStatusFalse():
	global status, water
	if status == True:
		status = False
		closePin(water)
		print ("Watering... Status: " + str(status))
		logging.debug("Watering... Status: " + str(status))		

def flowMeter():
	global pouring,lastPinState,pinState,lastPinChange,pinChange
	global pinDelta,hertz,flow,litersPoured,pintsPoured,currentTime	
	if(pinState != lastPinState and pinState == True):
		if(pouring == False):
			pourStart = currentTime
	pouring = True
	# get the current time
	pinChange = currentTime
	pinDelta = pinChange - lastPinChange
	if (pinDelta < 1000):
		# calculate the instantaneous speed
		hertz = 1000.0000 / pinDelta
		flow = hertz / (60 * 7.5) # L/s
		litersPoured += flow * (pinDelta / 1000.0000)
		pintsPoured = litersPoured * 2.11338
	if (pouring == True and pinState == lastPinState and (currentTime - lastPinChange) > 3000):
		pouring = False
	if (pintsPoured > 0.1):
		pourTime = int((currentTime - pourStart)/1000) - 3
		tweet = 'Someone just poured ' + str(round(pintsPoured,2)) + ' pints of root beer in ' + str(pourTime) + ' seconds'
		t.statuses.update(status=tweet)
		litersPoured = 0
		pintsPoured = 0		
	lastPinChange = pinChange
	lastPinState = pinState			
	
if __name__ == '__main__':     # Program start from here
  setGlobals()
  global now, currentTime

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
        logging.info(now)
        print ("Time is :" + str(now))
        getStatus()              
        if sendDataMorningTime < now < sendDataNightTime and sendDataMorningBit == False:
            sendDataMorningBit = True
            print ("Send Data at Morning")
        elif sendDataNightTime < now and sendDataNightBit == False:
            sendDataNightBit = True
            print ("Send Data at Night")
        elif now < restartTime and sendDataMorningBit == True:
            sendDataNightBit = False
            sendDataMorningBit = False	
            print ("Reset onSend Counters")	
        time.sleep(2) 	
        getAndWrite()
        currentTime = int(time.time() * 1000)
        if GPIO.input(22):
            pinState = True
        else:
            pinState = False
        flowMeter()			
  except KeyboardInterrupt:
    print ("Exiting Safely")
    closePin(water)
    time.sleep(2) 
    GPIO.cleanup() 
