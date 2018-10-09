import time
import os

COUNT = 20

cmd1 = "python imager.py -i -cfg perseus_3.12.bit"

cmd2 = "python imager.py -s1 -e1 220 -s2 -e2 200 -s3 -e3 200 -th -raw"
initTime = 0
captureTime = 0
for i in range(COUNT):

    os.system("clear")
    time.sleep(5)
    print("LOOP {}".format(i+1))
    print(cmd1)
    t1a = time.time()
    os.system(cmd1)
    t1b = time.time()
    initTime += (t1b-t1a)  
    time.sleep(2)
    t2a = time.time()
    os.system(cmd2)
    t2b = time.time()  
    captureTime += (t2b- t2a) 

print ("INITIALIZATION time = {} seconds".format(initTime/(COUNT*1.0)))

print ("CAPTURE time for 3 sensors  = {} seconds".format(captureTime/(COUNT * 1.0)))






