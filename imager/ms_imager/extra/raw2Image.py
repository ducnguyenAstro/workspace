
# coding: utf-8

# In[ ]:


#Convert 12 bit raw files into image shape
import numpy as np

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

