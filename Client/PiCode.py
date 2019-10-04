# Some libraries here
import requests
import random
import time

import time

#from board import SCL, SDA
#import busio

#from adafruit_seesaw.seesaw import Seesaw

#Define correct connection for i2c sensor
#i2c_bus = busio.I2C(SCL, SDA)

#ss = Seesaw(i2c_bus, addr=0x36)

#setup time loop
i = 0

#params
deviceid = 1

while(True):
    
    
    # read moisture level through capacitive touch pad
    #moisture = ss.moisture_read()
    moisture = 200

    # read temperature from the temperature sensor
    #temp = ss.get_temp()
    temp = 21
    
    #create a value to post
    #value = 21 + random.randint(1,2) + random.randint(1,10)/10
    #print("value to insert: "+str(value))
    
    
    #send a temp request
    url = "https://garden-project.herokuapp.com/insertall/"
    msg = url+str(deviceid)+'/1/"temp"/'+str(temp)
    r = requests.post(msg)

    #Log message:
    message = "Sent POST request to: "+msg
    print(message)
    print(r)

    #send a moisture request

    url = "https://garden-project.herokuapp.com/insertall/"
    msg = url+str(deviceid)+'/2/'moisture'/'+str(moisture)
    r = requests.post(msg)

    #Log message:
    message = "Sent POST request to: "+msg
    print(message)
    printcd

    #wait for a minute before looping
    i += 1
    time.sleep(2)

