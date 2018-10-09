import numpy as np
import glob
import os
from PIL import Image
import time

def rightShiftInLine(tiffLine,nOfBits):  # for one 16bit integer line

    tmpStr = ''.join([np.binary_repr(i>>4, width=12) for i in tiffLine])

    newStr = ''
    for i in range(nOfBits):
        newStr +='0'
    newStr += tmpStr    # Done padding zeros infront

    int16Arr = np.array([],dtype=np.int16)
    for i in range(len(newStr)//12):
        #rint(int(newStr[12*i : 12 *(i+1)],2)*16)
        int16Arr = np.append(int16Arr, int(newStr[12*i : 12 *(i+1)],2)*16)
    
    return int16Arr

def bitRightShift(tiffFile,nOfBits):
    # tiffFile(16bit) image
    # nOfBits: number of shifted bits to the right
    
    #load TiffImage
    img = Image.open(tiffFile)
    inArr = np.array(img)
    [row,col] = inArr.shape
    print(row,col)

    print('mean = {}, min = {}'.format(inArr.mean(), inArr.min()))
    
    outArr = np.zeros(0, dtype=np.int16)     # initialize the output Image ndarray
    for i in range(row):
        #print (rightShiftInLine(inArr[i,:],nOfBits))
        outArr = np.append(outArr,rightShiftInLine(inArr[i,:],nOfBits))
    
    print(outArr[:])
    print(outArr.shape)
    
    
    return outArr    # 16 bit data nparray

def main():
    nOfBits = 0
    tiffFile = '/home/usrp/workspace/imager/ms_imager/raw_files/sensor2_E100_G5_Modesto2_portion.tiff'
    shifted_data = bitRightShift(tiffFile, nOfBits)
    shifted_data.astype('int16').tofile(tiffFile[:-5] + '.16b_3')
    
    command = "raw2tiff -w 927 -l 564 -c lzw:2 -d short -M " #.format(col,row)
    command += tiffFile[:-5] + '.16b_3' + " "
    command += tiffFile[:-5] + "_{}shited.tiff".format(nOfBits)
    print(command)
    rc = os.system(command)
    print(rc)

if __name__ == "__main__":
    t1 = time.time()
    main()
    print('Elapsed time: {} seconds'.format(time.time()-t1))
