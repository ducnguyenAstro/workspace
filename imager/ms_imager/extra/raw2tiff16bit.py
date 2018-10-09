import glob
import os
from ctypes import *
from tiff_tag import *


libFile = glob.glob(os.getcwd()+'/libcutils4py.so')
print libFile

cLib = cdll.LoadLibrary(libFile[0])
#print cLib.type

#files = glob.glob(os.getcwd()+'/media/usrp/7c66e760-7591-4d67-b126-31392fef0921//imager/sensor*/*.raw')

files = glob.glob(os.getcwd()+'/sensor*/*.raw')

files.sort()

buf16 = create_string_buffer(141920000)

for filename in files:
    print ("File: "+filename)
    if not os.path.exists(filename[:-4] + ".tiff"):
	print "processing"
	with open(filename, "r") as myfile:
	    data = myfile.read()
	cLib.save_as_16bit(data,buf16,106439680)
	f = open(filename[:-4]+".16","wb")
	f.write(buf16)
	f.close()
	command = "raw2tiff -w 10000 -l 7096 -c lzw:2 -d short -M "
	tmpfile = filename[:-4] + ".16" 
	command += tmpfile + " "
	command += filename[:-4] + ".tiff"
	print command
	os.system(command)
	if os.path.isfile(tmpfile):
            os.remove(tmpfile)	

	command = "tiffset -sf " + str(TIFFTAG_IMAGEDESCRIPTION) + " "
	tmpfile = filename[:-4] + ".raw_tag"
	command += tmpfile + " "
	command += filename[:-4] + ".tiff"
	print command
	os.system(command)
