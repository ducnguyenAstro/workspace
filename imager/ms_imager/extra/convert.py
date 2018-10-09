#!/usr/bin/python
import glob
import os
from ctypes import *
#from tiff_tag import *


cLib = cdll.LoadLibrary(os.path.dirname(__file__)+'../libcutils4py.so')
#files = glob.glob('/mnt/ssd/imager/*/*.raw')
#files = glob.glob('/media/billy/Seagate Expansion Drive/AltlasBC-EM3 (ArielUnit)/0720Plane/sensor2/*.raw')
#files = glob.glob('/media/billy/959730fa-1b2e-4808-9637-21d14bcb81511/0721Plane/*/*.raw')

#files = glob.glob(os.getcwd()+'/sensor*/*.raw')
files = glob.glob('/mnt/ssd/imager/sensor1/*.raw')
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
'''
	command = "tiffset -sf " + str(TIFFTAG_IMAGEDESCRIPTION) + " "
	tmpfile = filename[:-4] + ".raw_tag"
	command += tmpfile + " "
	command += filename[:-4] + ".tiff"
	print command
	os.system(command)
	#if os.path.isfile(tmpfile):
	#    os.remove(tmpfile)	
'''
