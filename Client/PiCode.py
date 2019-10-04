# Some libraries here
import requests
import random
import time

import time

from board import SCL, SDA
import busio

from adafruit_seesaw.seesaw import Seesaw

#Define correct connection for i2c sensor
i2c_bus = busio.I2C(SCL, SDA)

ss = Seesaw(i2c_bus, addr=0x36)

#setup time loop
i = 0

while(True):
    
    
    # read moisture level through capacitive touch pad
    touch = ss.moisture_read()

    # read temperature from the temperature sensor
    temp = ss.get_temp()
    
    
    #create a value to post
    #value = 21 + random.randint(1,2) + random.randint(1,10)/10
    #print("value to insert: "+str(value))
    
    value = temp
    
    #send a request
    url = "https://garden-project.herokuapp.com/insert/"
    r = requests.post(url+str(value))

    #Log message:
    message = "Sent POST request to "+str(url)+" with value: "+str(value)
    print(message)

    #wait for a minute before looping
    i += 1
    time.sleep(2)

print("Aren't you bored?")