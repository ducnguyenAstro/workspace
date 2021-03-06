{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": 146,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "564 927\n",
      "mean = 31683.63493921519, min = 8192\n",
      "[29936 30432 30048 ... 35408 34752 35904]\n",
      "(522828,)\n",
      "raw2tiff -w 927 -l 564 -c lzw:2 -d short -M /home/usrp/workspace/imager/ms_imager/raw_files/sensor2_E100_G5_Modesto2_portion.16b_3 /home/usrp/workspace/imager/ms_imager/raw_files/sensor2_E100_G5_Modesto2_portion_0shited.tiff\n",
      "0\n",
      "Elapsed time: 4.341803312301636 seconds\n"
     ]
    }
   ],
   "source": [
    "# better run on Python 3 \n",
    "import numpy as np\n",
    "import glob\n",
    "import os\n",
    "from PIL import Image\n",
    "import time\n",
    "\n",
    "def rightShiftInLine(tiffLine,nOfBits):  # for one 16bit integer line\n",
    "    #tmpList = []\n",
    "    #tmpList += [np.binary_repr(i>>4, width=12) for i in tiffLine] \n",
    "    #print(tiffLine.shape)\n",
    "    tmpStr = ''.join([np.binary_repr(i>>4, width=12) for i in tiffLine])\n",
    "\n",
    "    newStr = ''\n",
    "    for i in range(nOfBits):\n",
    "        newStr +='0'\n",
    "    newStr += tmpStr    # Done padding zeros infront\n",
    "\n",
    "    int16Arr = np.array([],dtype=np.int16)\n",
    "    for i in range(len(newStr)//12):\n",
    "        #rint(int(newStr[12*i : 12 *(i+1)],2)*16)\n",
    "        int16Arr = np.append(int16Arr, int(newStr[12*i : 12 *(i+1)],2)*16)\n",
    "    \n",
    "    return int16Arr\n",
    "\n",
    "def bitRightShift(tiffFile,nOfBits):\n",
    "    # tiffFile(16bit) image\n",
    "    # nOfBits: number of shifted bits to the right\n",
    "    \n",
    "    #load TiffImage\n",
    "    img = Image.open(tiffFile)\n",
    "    inArr = np.array(img)\n",
    "    [row,col] = inArr.shape\n",
    "    print(row,col)\n",
    "    #print(inArr[:10,:10])\n",
    "    #print(data.shape)\n",
    "    print('mean = {}, min = {}'.format(inArr.mean(), inArr.min()))\n",
    "    \n",
    "    outArr = np.zeros(0, dtype=np.int16)     # initialize the output Image ndarray\n",
    "    for i in range(row):\n",
    "        #print (rightShiftInLine(inArr[i,:],nOfBits))\n",
    "        outArr = np.append(outArr,rightShiftInLine(inArr[i,:],nOfBits))\n",
    "    \n",
    "    print(outArr[:])\n",
    "    print(outArr.shape)\n",
    "    \n",
    "    # SHOULD DUMP THEM AS A SEQUENCE THEN USE RAW2TIFF\n",
    "    \n",
    "    return outArr    # 16 bit data image\n",
    "    #Image.fromarray(outArr).save('/home/usrp/workspace/imager/ms_imager/raw_files/sensor2_E100_G5_Modesto2_portion.png')\n",
    "    #return True #outImage\n",
    "    #for i in range(len(tiffFile)):\n",
    "        \n",
    "def main():\n",
    "    nOfBits = 0\n",
    "    tiffFile = '/home/usrp/workspace/imager/ms_imager/raw_files/sensor2_E100_G5_Modesto2_portion.tiff'\n",
    "    shifted_data = bitRightShift(tiffFile, nOfBits)\n",
    "    shifted_data.astype('int16').tofile(tiffFile[:-5] + '.16b_3')\n",
    "    \n",
    "    command = \"raw2tiff -w 927 -l 564 -c lzw:2 -d short -M \" #.format(col,row)\n",
    "    command += tiffFile[:-5] + '.16b_3' + \" \"\n",
    "    command += tiffFile[:-5] + \"_{}shited.tiff\".format(nOfBits)\n",
    "    print(command)\n",
    "    rc = os.system(command)\n",
    "    print(rc)\n",
    "    '''\n",
    "    try:\n",
    "        files = glob.glob(os.getcwd()+'/raw_files/sensor3_E100_G5_Modesto4_16bitPortion') \n",
    "        bitRightShift(files[0])\n",
    "    except:\n",
    "        print (\"Can not find images\")\n",
    "   ''' \n",
    "if __name__ == \"__main__\":\n",
    "    t1 = time.time()\n",
    "    main()\n",
    "    print('Elapsed time: {} seconds'.format(time.time()-t1))"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.6.5"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 2
}
