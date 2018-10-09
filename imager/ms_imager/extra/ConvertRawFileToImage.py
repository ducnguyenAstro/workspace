
#Convert 12 bit raw files into image shape
import numpy as np
from PIL import Image 
import time

HEIGHT = 7096
WIDTH = 10000

def read_uint12(imageRaw,height,width):   # convert raw bit file into imageTrue file

    data=np.fromfile(imageRaw, dtype=np.uint8)
    data=np.unpackbits(data)
    lent = data.shape[0] - np.remainder(data.shape[0],12)
    data=data[:lent].reshape((int(lent/12),12))

    imageTrue=np.zeros(data.shape[0],dtype=np.uint16)   # initialize ImageTrue: is right value of Image
    for i in range(0,12):
        imageTrue+=2**i*data[:,11-i]

    imageTrue = np.resize(imageTrue,(height,width))
    return imageTrue

def saveImage(imageTrue, imageName):
    im = Image.fromarray(imageTrue)
    im.save(imageName)
    
if __name__ == "__main__":
    t1 = time.time()
    rawFile = '/home/usrp/workspace/imager/ms_imager/raw_files/BC3/sensor2_E100_G5_Modesto2.raw'
    imageName = '/home/usrp/workspace/imager/ms_imager/raw_files/BC3/sensor2_E100_G5_Modesto2_01.tif'
    saveImage(read_uint12(rawFile, HEIGHT, WIDTH), imageName)
   
    #main()
    print('Elapsed time: {} seconds'.format(time.time()-t1))
