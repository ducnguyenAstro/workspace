# Column diference
import numpy as np
import os
from PIL import Image
import glob
import time

#dirPath = os.getcwd()
#fileName = dirPath + "/sensor2_E100_G5_Modesto2.tiff"


try:
    files = glob.glob(os.getcwd()+'/raw_files/*.tiff') 
    print("processing")
    t1 = time.time()
except:
    print ("Can not find images")
   

files.sort()
fileStat = np.array(['file Name', ' min', ' max', ' average', ' standard deviation'])

HEIGHT_TEST = 1000

f = open("ghostCheking" + time.strftime("%j%H%M%S", time.gmtime()), "w")

for fileName in files:
    
    img = Image.open(fileName)
    imgArr = np.array(img)/16

    [row,col] = imgArr.shape
    a = np.array([])
    
    for i in range(col-1):
        temp =np.abs(imgArr[:HEIGHT_TEST,i]-imgArr[:HEIGHT_TEST,i+1])
        a = np.append(a,np.average(temp))
    
    fileStat = np.append(fileStat,[fileName, np.min(a), np.max(a), np.average(a), np.std(a) ])
    #f.write(fileName + str(np.min(a)) +str(np.max(a)) + str(np.average(a)) + str(np.std(a) + "\n"))

t2 = time.time()    
f.write(np.array2string(fileStat,separator = '    '))
f.write("\n \nElapsed in : {} seconds".format(t2-t1))

f.close()
 
#print(fileStat)
print("Completed : {} seconds".format(t2-t1))  
