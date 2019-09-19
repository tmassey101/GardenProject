# Some libraries here
import requests
import random
import time

#setup time loop
for i in range(1000):
    
    time.sleep(60)

    #create a value to post
    value = 20 + random.randint(1,2) + random.randint(1,10)/10
    print("value to insert: "+str(value))

    #send a request
    url = "https://garden-project.herokuapp.com/insert/"
    r = requests.post(url+str(value))

    #Log message:
    message = "Sent POST request to "+str(url)+" with value: "+str(value)
    print(message)

print("Aren't you bored?")