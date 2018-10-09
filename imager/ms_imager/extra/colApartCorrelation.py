#!/usr/bin/env python
# coding: utf-8


# check correlation of apart Column
import numpy as np
import math
import os
from PIL import Image
import glob
import time

#dirPath = os.getcwd()
#fileName = dirPath + "/sensor2_E100_G5_Modesto2.tiff"

def mean(someList):
    total = 0
    for a in someList:
        total += float(a)
    mean = total/len(someList)
    return mean
def standDev(someList):
    listMean = mean(someList)
    dev = 0.0
    for i in range(len(someList)):
        dev += (someList[i]-listMean)**2
    dev = dev**(1/2.0)
    return dev
def correlCo(someList1, someList2):

    # First establish the means and standard deviations for both lists.
    xMean = mean(someList1)
    yMean = mean(someList2)
    xStandDev = standDev(someList1)
    yStandDev = standDev(someList2)
    # r numerator
    rNum = 0.0
    for i in range(len(someList1)):
        rNum += (someList1[i]-xMean)*(someList2[i]-yMean)

    # r denominator
    rDen = xStandDev * yStandDev

    r =  rNum/rDen
    return r

def colCorr (fileName, numberOfBits, startCol, WIDTH_TEST, HEIGHT_TEST ):      # calculate correllation coefficiences of numberOfBits apart columns in lower right area WIDTH_TEST * HEIGHT_TEST
    img = Image.open(fileName)
    imgArr = np.array(img)/16    # store 12 bit value on ndarray
    [row,col] = imgArr.shape
    
    a = np.array([])    # initialize ndarry to store correlation coeffciences of each column
    
    leftCornerCol = 3000
    leftCornerRow = 3000

    try:
        for i in range( leftCornerCol, leftCornerCol + WIDTH_TEST - numberOfBits ):
            temp =np.corrcoef(imgArr[leftCornerRow:(leftCornerRow + HEIGHT_TEST),i], imgArr[leftCornerRow:(leftCornerRow + HEIGHT_TEST), i+numberOfBits])
            a = np.append(a,temp[1,0])

    # NOT using Numpy
    '''
            a1 = imgArr[leftCornerRow:(leftCornerRow + HEIGHT_TEST),i].tolist()
            a2 = imgArr[leftCornerRow:(leftCornerRow + HEIGHT_TEST), i+numberOfBits].tolist()
        
            temp =np.corrcoef(a1,a2)
            print (temp)
            a = np.append(a,temp[1,0])  '''
        return [np.min(a), np.max(a), np.mean(a), np.std(a)]  # return min, max, mean and standard deviation off the image
    
    except:
        return [0,0,0,0]
    
# test for module when run in isolation

def main():
    try:
        files = glob.glob(os.getcwd()+'/raw_files/BC3/*.tiff') 
        BITS = 16
        print("{} Columns apart correllation".format(BITS))
        print("processing")
        t1 = time.time()
    except:
        print ("Can not find images")

    files.sort()
        
    fileStat = 'file Name' + '\t Min  \t Max \t Mean \t Standard Deviation: \n'
    for fileName in files:
        fileStat = fileStat + fileName + '\t' + '\t'.join(str(x) for x in colCorr(fileName, BITS, 100, 1000, 1000)) + '\n'
    
    t2 = time.time()
    
    #print(fileStat)
    print("Completed in: {} seconds".format(t2-t1))
    f = open("{}BitsApartColCorrCheck".format(BITS) + time.strftime("%j%H%M%S", time.gmtime()), "w")   
    f.write(fileStat)
    f.write("\n \nElapsed in : {} seconds".format(t2-t1))
    f.close()
    
if __name__ == "__main__":
   main()




