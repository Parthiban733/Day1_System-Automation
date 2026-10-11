import csv
import random
import time


i = 0 
with open('DAY2_HISTORY.csv', 'w', newline='') as csvfile:
    fieldnames = ['Temprature', 'Pressure', 'Vibration', 'RPM','Current','State']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
        
    for i in range(1,150):
        tm = random.randint(50, 95)   # TODO
        pr = random.randint(20, 90)     # TODO
        vb = random.uniform(0.0, 1.0)
        rp =  random.uniform(0.0, 1000)
        cu = random.uniform(0,20)
        st = random.choice(["Normal","Error"])
        writer.writerows([
     {'Temprature': tm, 'Pressure': pr, 'Vibration': vb, 'RPM': rp ,'Current':cu , 'State': st},
    ])


       
       