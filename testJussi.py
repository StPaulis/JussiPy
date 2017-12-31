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
	water = 21

def openPin(pin):
	GPIO.output(pin,GPIO.LOW)
	print ("openPin()")

def closePin(pin):
	GPIO.output(pin,GPIO.HIGH) 
	print ("closePin()")

def setup():
	print ("Start setup()")
	#GPIO.setmode(GPIO.BOARD) #Numbers GPIOs by physical location
	GPIO.setup(water, GPIO.OUT) 
	closePin(water)			             
		
def getValues(sp):
	print ("Start getValues()")
	global Liters,temp,hum
	if sp == 1:
		h = mcp.read_adc(0)
		hum = (1 - (float(h)/ 1023))* 200 
		print ("Humidity:" + str(hum))
	elif sp == 2:
		t = mcp.read_adc(1)
		temp = float(t) - 40
		print ("Temperature:" + str(temp))
	elif sp == 3:
		l = ("Liters: 0")
		Liters = 0
		print ("Running Liters: " + str(Liters))

def getValuesDigital(sp):
	print ("Start getValuesDig()")
	global Liters,temp,hum
	if sp < 3:
		h = mcp.read_adc(0)
		with SHT1x(18, 23, gpio_mode=GPIO.BCM) as sensor:
			temp = sensor.read_temperature() - 40
			hum = 1 - (sensor.read_humidity(temp) / 1023) * 100 
			sensor.calculate_dew_point(temp, hum)
			print(sensor)
		print ("Humidity:" + str(hum) + ", Temp:" + str(temp))
	elif sp == 3:
		l = ("Liters: 0")
		Liters = 0
		print ("Running Liters: " + str(Liters))		

# TODO:POst
def getAndWrite():
	print ("Start getAndWrite()")
	global hum,temp,Liters,status,data
	for x in range(1, 4):
		getValues(x)
		# getValuesDigital(x)
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
		print ("getStatus error")
	print (str(Upstatus) + " ... Server's status")
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

def changeStatusFalse():
	global status, water
	if status == True:
		status = False
		closePin(water)
		print ("Watering... Status: " + str(status))	
	
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
  except KeyboardInterrupt:
    print ("Exiting Safely")
    closePin(water)
    time.sleep(2) 
    GPIO.cleanup() 
