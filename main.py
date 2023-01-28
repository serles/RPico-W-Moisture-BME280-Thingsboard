from machine import SoftI2C, ADC, Pin, I2C
from sh1106 import SH1106_I2C
import framebuf
import utime
import urequests #as requests
import network, time
from uthingsboard.client import TBDeviceMqttClient
import os
from ntpTime import ntpTime
import bme280

soil = ADC(Pin(26)) #Soil moisture Pin reference

min_moisture=19200 #Calibration Values
max_moisture=49300

delayOLED = 3 #delay between readings standard 60
delayIoT = 6 #standard delay 360
delay_count = 0

#data connection
KEY = "KAAKFZ4SQAFI3D43"  
ssid = "NadahaWLAN"
password = "TSEuse74f5C7DK32h"

#display area
WIDTH  = 128 # oled display width
HEIGHT = 64  # oled display height

#connection & definition display
i2c=I2C(0,sda=Pin(0), scl=Pin(1), freq=400000)
oled = SH1106_I2C(WIDTH, HEIGHT, i2c)
oled.fill(0)

#connection to the BME280 sensor
i2c_soft = SoftI2C( sda=Pin(20), scl=Pin(21), freq=400000)
bme = bme280.BME280(i2c=i2c_soft) #BME280 object created

oled.text("Starte...", 0, 0)
oled.show()
utime.sleep(1)

#Configure Pico as Station
wlan=network.WLAN(network.STA_IF)
wlan.active(True)

#create path
file_path = '/logs/log.txt'

#function to read sensor data
def read_moisture():
    #read moisture value and convert to percentage into the calibration range
    moisture = round((max_moisture-soil.read_u16())*100/(max_moisture-min_moisture),2)
    return moisture

def send_Thingsboard(data="", temp="", pressure="", humidity=""):
    client = TBDeviceMqttClient('demo.thingsboard.io', access_token = KEY)
    client.connect()

    result = client.publish_data("v1/devices/me/telemetry", {"moisture":data},1)
    result = client.publish_data("v1/devices/me/telemetry", {"temperature":temp},1)
    result = client.publish_data("v1/devices/me/telemetry", {"pressure":pressure},1)
    result = client.publish_data("v1/devices/me/telemetry", {"humidity":humidity},1)
    client.disconnect()
    
def update_bme280_reading():
    print(bme.values)  
    svalues = {"temp": bme.values[0], "pressure": bme.values[1], "humidity": bme.values[2]}
    return svalues

def connect_wlan():
    max_wait = 5
    try:
        if not wlan.isconnected():
            print("connecting to network...")
            oled.fill(0)
            oled.text("connecting...", 0, 0)
            oled.show()
            wlan.connect(ssid,password)
            utime.sleep(1)
            # Wait for connect or fail 13 max_wait = 10
            while max_wait > 0:
                if wlan.status() < 0 or wlan.status() >= 3:
                    break
                max_wait -= 1
                print('waiting for connection...')
                utime.sleep(1)
            max_wait = 5    
            # same loop but disconnecting each time before reconnecting
            while max_wait > 0:
                if wlan.status() < 0 or wlan.status() >= 3:
                    break
                wlan.disconnect()
                max_wait -= 1
                print('reconnecting...')
                utime.sleep(2)
                wlan.connect(ssid,password)
                utime.sleep(2)
        
            if wlan.status() != 3:
                raise RuntimeError("network connection failed")
            else:
                print("connected")
                status = wlan.ifconfig()
                print( 'ip = ' + status[0] )
        else:
            print("is already connected")
        
        if wlan.status() == 3:
            print("network config:", wlan.ifconfig())
            try:
                #refresh RTC
                tm = ntpTime.setTimeRTC()
                machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
                print('date:', tm)
            except:
                pass
    except:
        oled.fill(0)
        oled.text("connection failed",5,0)
        oled.show()


def write_log(date, message, value1="", value2="", value3="", value4=""):
    file = open(file_path, "a")
    file.write(date + '\t' + message + '\t' + value1 + '\t' + value2 + '\t' + value3 + '\t' + value4 + '\n')
    file.close()

#call wlan connection for the first time
connect_wlan()
       
utime.sleep(1)
timestrg = ""
timestrgthingsboard = ""

while True:
    moisture = read_moisture()
    bme280 = {}
    bme280 = update_bme280_reading()
    temp = float(bme280["temp"])
    pressure = float(bme280["pressure"])
    humidity = float(bme280["humidity"])
    
    
    
    current_time = utime.localtime()
    timestrg = "%02d/%02d/%02d %02d:%02d:%02d" % (current_time[0], current_time[1], current_time[2], current_time[3], current_time[4], current_time[5])
    #send to thinkspeak
    if delay_count >= delayIoT:
        try:                    
            if wlan.isconnected():
                #send data to thingsboard
                print("sending...")
                send_Thingsboard(moisture, temp, pressure, humidity)
                timestrgthingsboard = "%02d:%02d:%02d" % (current_time[3], current_time[4], current_time[5])
                write_log(timestrg, 'ThingsB', str(moisture), str(temp) + "C", str(pressure) + "hPa", str(humidity) + "%")
                print ('time for thingsboard: ', timestrgthingsboard)
            else:
                print("wlan not connected")
                write_log(timestrg, 'wlan not connected')
                connect_wlan()
        except Exception as e:
            print("except thrown (status =" + str(wlan.status())+")")
            print(e.args)
            write_log(timestrg, e.args)
            if wlan.status() != 3:
                print("trying to reconnect...")
                write_log(timestrg, 'trying to reconnect')
                connect_wlan()
            else:
                print("wlan connection is fine")
        delay_count = 0
    
    #send to display
    oled.fill(0)
    oled.text("Tomato Plant",10,0)
    oled.text("m" + str("%.1f" % moisture)+"%",0,15)
    oled.text("t"+ "%.1f" % temp + "C",72,15)
    pressurekPa = pressure/10 #calc pressure from hPa to kPa
    oled.text("p"+ "%.1f" % pressurekPa + "kPa" ,0,30)
    oled.text("h"+ "%s" % humidity + "%",72,30)
    oled.text("sent: %s" % timestrgthingsboard,0,45)
    oled.show()
    print("M: ", moisture)
    print (str(temp) + "C")
    print (str(pressure) + "hPa")
    print (str(humidity) + "%")
    #write_log(timestrg, 'Display', str(moisture))
    utime.sleep(delayOLED)
    delay_count += delayOLED


##multithreading
#ray.get([IoT.remote(), display.remote()])