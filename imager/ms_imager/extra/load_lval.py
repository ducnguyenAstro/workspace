'''
Copyright 2015, Aquila Space Inc. All rights reserved.

This software is subject to U.S. Department of Commerce export regulations
under ECCN 9D515.

THIS SOFTWARE IS PROVIDED BY AQUILA SPACE INC. "AS IS" AND ANY EXPRESSED
OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
IN NO EVENT SHALL AQUILA SPACE INC. OR ITS CONTRIBUTORS BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
THE POSSIBILITY OF SUCH DAMAGE.
'''

import sys
import os
import time
import binascii
import py_configs
import logging
import argparse
from logging import handlers
from datetime import datetime
from sensor_adc import *
from fpga import *
from array import array
from ctypes import *
from tiff_tag import *
from adt import *
from uuid import getnode as get_mac
from libgps.gpsclient import *
from icasper import casper

# logging 
LOG_LEVEL = py_configs.PY_LOGS_LEVEL
LOG_FILENAME = py_configs.PY_LOGS_PATH + py_configs.PY_LOGS_FILENAME
LOG_FORMAT = py_configs.PY_LOGS_FORMAT
LOG_MAX_BYTES = py_configs.PY_LOGS_MAX_BYTES
LOG_FILE_COUNT = py_configs.PY_LOGS_MAX_FILE_COUNT
LOG_ADDRESS = py_configs.PY_LOGS_ADDRESS

formatter = logging.Formatter(LOG_FORMAT)
logger = logging.getLogger('IMAGER')
logger.setLevel(LOG_LEVEL)
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(LOG_LEVEL)
consoleHandler.setFormatter(formatter)
fileHandler = handlers.RotatingFileHandler(LOG_FILENAME,
                                           maxBytes=LOG_MAX_BYTES,
                                           backupCount=LOG_FILE_COUNT)
fileHandler.setLevel(LOG_LEVEL)
fileHandler.setFormatter(formatter)
socketHandler = handlers.SocketHandler(LOG_ADDRESS, handlers.DEFAULT_TCP_LOGGING_PORT)

logger.addHandler(socketHandler)
logger.addHandler(consoleHandler)
logger.addHandler(fileHandler)

THUMBNAIL_WIDTH = 1000
THUMBNAIL_HIGHT = 709
IMAGE_WAIT_TIMEOUT_CNT = 20

# image save folder
IMAGE_SAVE_PATH = "/mnt/ssd/imager/sensor"
RAW_DATA_FILENAME = "imager_data.bin"

class Imager(object):

    def __init__(self, test, sensors, count):
        self._file = ''
        #self.bufSize = SENSOR_BYTES_PER_FRAME
        #self.buf = bytearray(self.bufSize)
        #self.buf_16bit = bytearray(self.bufSize * 2 / 3)
        self.bufSize = c_uint(SENSOR_BYTES_PER_FRAME)
        self.buf = create_string_buffer(self.bufSize.value)
        self.buf_8bit = create_string_buffer(SENSOR_NUM_ROWS * SENSOR_NUM_COLUMNS)
        self.buf_16bit = create_string_buffer(SENSOR_NUM_ROWS * SENSOR_NUM_COLUMNS * 2)
        self.buf_thumb = create_string_buffer(THUMBNAIL_WIDTH * THUMBNAIL_HIGHT)
        self.cLib = cdll.LoadLibrary('./libcutils4py.so')
        self.isTestPattern = test # True or False
        self.fpga = Fpga()
        self.sensor1 = None
        self.sensor1_on = False
        self.sensor2 = None
        self.sensor2_on = False
        self.sensor3 = None
        self.sensor3_on = False
        self.timeStamp = ''
        self.filename = ""
        self.tiff = False
        self.raw = False
        self.writetiff = True
        self.thumbnail = False
        self.casper = False
        self.bitfile = ''
        self.check = False
        self.tag = Tag()
        self.adt = Adt()
        self.sensors = sensors
        try:
            self.gpsp = GpsPoller()
            self.gpsp.start()
        except:
            logger.error("GPSD Not Running, GPS link failed")
            pass
        self.acsdat = ""
        self.test = 0

        #gps variables.
        self.gpsOn = False
        self.latitude = None
        self.longitude = None
        self.utc = None
        self.time = None
        self.altitude = None
        self.etc = None


        if self.sensors & 0x1:
            self.sensor1 = Sensor(0)
            directory = IMAGE_SAVE_PATH + "1"
            if not os.path.exists(directory):
                os.makedirs(directory)
        if self.sensors & 0x2:
            self.sensor2 = Sensor(1)
            directory = IMAGE_SAVE_PATH + "2"
            if not os.path.exists(directory):
                os.makedirs(directory)
        if self.sensors & 0x4:
            self.sensor3 = Sensor(2)
            directory = IMAGE_SAVE_PATH + "3"
            if not os.path.exists(directory):
                os.makedirs(directory)
        self.image_count = count
    
    def convert_to_8bit_tiff(self, sensorId, srcFile):
        logger.info("Func() : " + sys._getframe().f_code.co_name)
        dstFile = IMAGE_SAVE_PATH + str(sensorId+1) + "/sensor" + str(sensorId+1) + "_" + self.timeStamp + "_8bit"
        dstFile += ".tiff"
        command = "./raw2tiff -w 10000 -l 7096 -c lzw:2 -M "
        command += srcFile + " " 
        command += dstFile
        os.system(command)
        logger.info(command)

    def convert_to_16bit_tiff(self, sensorId, srcFile):
        logger.info("Func() : " + sys._getframe().f_code.co_name)
        if (sensorId == 0):
            sensor = self.sensor1
        elif(sensorId == 1):
            sensor = self.sensor2
        else:
            sensor = self.sensor3    
       
        dstFile = IMAGE_SAVE_PATH + str(sensorId+1) + "/sensor" + str(sensorId+1) + "_" + self.timeStamp + "_16bit"
        if (self.filename != ""):
            dstFile = self.CalFilename(sensorId)
        dstFile += ".tiff"
        command = "./raw2tiff -w 10000 -l 7096 -c lzw:2 -d short -M "
        command += srcFile + " " 
        command += dstFile
        os.system(command)        
        logger.info(command)
        
        #make image description
        self.make_tag(sensorId)
        
        # write image description to tiff file
        tagFile = dstFile + TIFFTAG_FILE_EXT 
        self.tag.flush_to_file(tagFile)
        command = "./tiffset -sf " + str(TIFFTAG_IMAGEDESCRIPTION) + " "
        command += tagFile + " "
        command += dstFile
        os.system(command)  
        self.tag.remove_file()      
        logger.info(command)

    def convert_to_thumb_tiff(self, sensorId, srcFile):
        logger.info("Func() : " + sys._getframe().f_code.co_name)
        dstFile = IMAGE_SAVE_PATH + str(sensorId+1) + "/sensor" + str(sensorId+1) + "_" + self.timeStamp + "_thumb"
        if (self.filename != ""):
            dstFile = self.CalFilename(sensorId)+"_thumb"
        dstFile += ".tiff"
        command = "./raw2tiff -w 1000 -l 709 -c lzw:2 -M "
        command += srcFile + " " 
        command += dstFile
        os.system(command)
        logger.info(command)
        #DNif self.check:   
        self.ghost_reset(sensorId, dstFile)

    def exit_app(self, description):
        logger.error(description)
        #sys.exit("program ended unexpectedly due to an error")

    def ghost_reset(self, sensorId, dstFile):
        logger.info("Func() : " + sys._getframe().f_code.co_name + " Checking Sensor#: "+str(sensorId))
        logger.warning("Func() : " + sys._getframe().f_code.co_name + " Checking Sensor#: "+str(sensorId))  # DN added
        if (not self.casper): #if already caspered, no need to check rest of images
            if casper(dstFile):
                self.casper = True
        if (sensorId == 2 and self.casper):
            rc = self.fpga.reset()
            if rc != ErrorCode.NoError:
                self.exit_app("fpga reset rc=" + str(rc))
            logger.info("Resetting FPGA")
            self.casper = False
        elif (sensorId == 2 and not self.casper):
            self.check = False

    def init_fpga(self, bitfile):
        rc = self.fpga.get_devInfo()
        if rc != ErrorCode.NoError:
            self.exit_app("get device info error rc=" + str(rc))

        # print dev count, name, id and serial number
        self.fpga.print_devInfo()

        # clear registers in FPGA
        self.fpga.clear_registers()

        # set VIO
        self.fpga.set_vio()

        if bitfile:
            # configure bit file
            rc = self.fpga.configure(bitfile, True)            
        else:
            self.fpga.is_configured()
            logger.info("no option to configure bitfile")
            
        if rc != ErrorCode.NoError:
            self.exit_app("fpga configuration rc=" + str(rc))

        # power on sensor
        self.fpga.control_power_sensor(True)

        # reset sensor
        self.fpga.reset_sensor()

        # download reg.bin file
        if self.sensor1 != None:
            self.sensor1.configure()
        if self.sensor2 != None:
            self.sensor2.configure()
        if self.sensor3 != None:
            self.sensor3.configure()

        # set number of frames in burst and enable internal sequencer
        if self.sensor1 != None:
            self.sensor1.set_init_mode()
        if self.sensor2 != None:
            self.sensor2.set_init_mode()
        if self.sensor3 != None:
            self.sensor3.set_init_mode()

        # reset adc and set 1-lane 12 bit mode
        if self.sensor1 != None:
            self.sensor1.reset_adc()
        if self.sensor2 != None:
            self.sensor2.reset_adc()
        if self.sensor3 != None:
            self.sensor3.reset_adc()

        # reset memory controller
        rc = self.fpga.reset_memoryController()
        if rc != ErrorCode.NoError:
            self.exit_app("fpga reset memoryController rc=" + str(rc))

        # set write buffer address
        rc = self.fpga.set_write_buf_address()

        # reset fpga
        rc = self.fpga.reset()
        if rc != ErrorCode.NoError:
            self.exit_app("fpga reset rc=" + str(rc))
        time.sleep(1)

        print (" *** set register ***")
        rc = self.fpga.set_register(rS1Enable, 1)
        if rc != ErrorCode.NoError:
            self.fpga.exit_app("set_register() rc=" + str(rc))


    def get_timeStamp(self):
        logger.info("Func() : " + sys._getframe().f_code.co_name)
        self.timeStamp = time.strftime("%m%d-%H%M%S")

    def reset_memory(self):
        logger.info("Func() : " + sys._getframe().f_code.co_name)
        self._fpga.reset_memoryController()

    def readcal(self, filename):
        try:
            with open(filename, 'r') as myfile:
                return myfile.read().replace(',', '-')
        except:
            return ""

    def make_tag(self, sensorId):
        logger.info("Func() : " + sys._getframe().f_code.co_name)
        if (sensorId == 0):
            sensor = self.sensor1
            linecal = self.readcal('calcoefficient1.dat')
        elif(sensorId == 1):
            sensor = self.sensor2
            linecal = self.readcal('calcoefficient2.dat')
        else:
            sensor = self.sensor3
            linecal = self.readcal('calcoefficient3.dat')
                    
        exposure = sensor.get_exposure()
        gain = sensor.get_gain()
        temp = sensor.read_temperature()
        logger.info("Func() : Sensor Chip Temperature is: "+str(temp)+" C")
        tagtemp1 = self.adt.digitize(1, 3380, sensorId+1) #sensor & adc
        tagtemp2 = self.adt.digitize(2, 3936, 0) #all other 5 thermistors 
        logger.info("Func() : tagtemp1 and tagtemp2: "+str(tagtemp1)+","+str(tagtemp2))
        self.tag.write_tag("UUID=" + str(hex(get_mac())))
        self.tag.write_tag("Sensor ID=" + str(sensorId+1))
        self.tag.write_tag("Date=" + self.timeStamp)
        self.tag.write_tag("exposure=" + str(exposure))        
        self.tag.write_tag("gain=" + str(gain))
        self.tag.write_tag("temperature=" + str(temp))
        self.tag.write_tag(tagtemp1)
        self.tag.write_tag(tagtemp2)
        self.tag.write_tag("TimeStamp="+str(time.time()))
        self.tag.write_tag("Second="+str(self.fpga.second)+", SubSecond="+str(self.fpga.subsecond))
        self.tag.write_tag("LineCal="+linecal)
        self.tag.write_tag(self.acsdat)
        if self.gpsOn:
            self.tag.write_tag(self.latitude + ", " + self.longitude + ", " + self.utc + ", " + self.time + ", " + self.altitude)
            self.tag.write_tag(self.etc)

    def gps_update(self):
        self.latitude = str(self.gpsp.gpsd.fix.latitude)
        self.longitude = str(self.gpsp.gpsd.fix.longitude)
        self.utc = str(self.gpsp.gpsd.utc)
        self.time = str(self.gpsp.gpsd.fix.time)
        self.altitude = str(self.gpsp.gpsd.fix.altitude)

        self.etc = str(self.gpsp.gpsd.fix.eps) + ", "
        self.etc = self.etc + str(self.gpsp.gpsd.fix.epx) + ", "
        self.etc = self.etc + str(self.gpsp.gpsd.fix.ept) + ", "
        self.etc = self.etc + str(self.gpsp.gpsd.fix.speed) + ", "
        self.etc = self.etc + str(self.gpsp.gpsd.fix.climb) + ", "
        self.etc = self.etc + str(self.gpsp.gpsd.fix.track) + ", "
        self.etc = self.etc + str(self.gpsp.gpsd.fix.mode)
        logger.info("Func() : Latitude is: " + self.latitude)
        logger.info("Func() : Longitude is: " + self.longitude)
        logger.info("Func() : Altitude is: " + self.altitude)
         
    def make_thumbnail(self, sensorId):
        logger.info("Func() : " + sys._getframe().f_code.co_name)
         # write to a file
        logger.info(str(datetime.now()))
        for i in range(0, THUMBNAIL_HIGHT):
            for j in range(0, THUMBNAIL_WIDTH):
                index = (j + i*SENSOR_NUM_COLUMNS)*(SENSOR_NUM_COLUMNS/THUMBNAIL_WIDTH)*3/2
                self.buf_thumb[j+i*THUMBNAIL_WIDTH] = self.buf[index]

        logger.info(str(datetime.now()))
        file_name_thumb = RAW_DATA_FILENAME + "_thumb"
        f = open(file_name_thumb, "wb")
        f.write(self.buf_thumb)
        f.close()
        self.convert_to_thumb_tiff(sensorId, file_name_thumb) 

    def save_as_16bit(self):
        logger.info("Func() : " + sys._getframe().f_code.co_name)
        
        for i in xrange(0, len(self.buf) - 3, 3): 
            pixel = self.buf[i] * 16 + (self.buf[i+1] & 0xF0) >> 4
            self.buf_16bit[i*2/3] = (pixel & 0xFF0) >> 4
            pixel = ((self.buf[i+1] & 0x0F) * 256 + self.buf[i + 2])
            self.buf_16bit[i*2/3+1] = (pixel & 0xFF0) >> 4      

    def swap_bytes(self):
        logger.info("Func() : " + sys._getframe().f_code.co_name)
        # Every group of four bytes has to be swapped.
        for i in xrange(0, len(self.buf) - 4, 4): 
            x = self.buf[i]
            self.buf[i] = self.buf[i + 3]
            self.buf[i + 3] = x
            x = self.buf[i + 1]
            self.buf[i + 1] = self.buf[i + 2]
            self.buf[i + 2] = x

    def is_imageReady(self):
        logger.info("Func() : " + sys._getframe().f_code.co_name)
        if self.sensor1_on == True:
            rc, regval = self.fpga.get_register(rS1LineCount)
            if regval != 7096:
                return False
        if self.sensor2_on == True:
            rc, regval = self.fpga.get_register(rS2LineCount)
            if regval != 7096:
                return False
        if self.sensor3_on == True:
            rc, regval = self.fpga.get_register(rS3LineCount)
            if regval != 7096:
                return False
        return True 

    def take_picture(self):
        logger.info("Func() : " + sys._getframe().f_code.co_name)

        # clear error and lock status
        rc = self.fpga.set_register(rClearErrors, 1)
        rc = self.fpga.set_register(rRstLock, 1)

        # set memory write enable
        rc = self.fpga.set_register(rMemWr, 1)
        if rc != ErrorCode.NoError: 
            self.exit_app("setting memory write enable rc=" + str(rc))

        # set SEQ_START bit.
        rc = self.fpga.toggle_register(rSeqStart, False, 0.1)
        if rc != ErrorCode.NoError: 
            self.exit_app("setting SEQ_START bit rc=" + str(rc))

        #make sure we get GPS right afterwards.
        if self.gpsOn:
            try:
                self.gps_update()
            except:
                logger.error("GPSD Not Running, GPS link failed")
                pass

        # wait until image is ready or timeout
        wait_count = 0
        while True: 
            time.sleep(0.1)
            wait_count += 1
            if self.is_imageReady() == True:
                break
            if wait_count == IMAGE_WAIT_TIMEOUT_CNT:
                logger.error("Image is not ready : timeout")
                break

        # read error and lock status : register 0x20
        rc = self.fpga.read_status()

        # turn off memory write enable
        rc = self.fpga.set_register(rMemWr, 0)
        if rc != ErrorCode.NoError:
            self.exit_app("turning off memory write enable rc=" + str(rc))

        # get time stamp 
        self.get_timeStamp()

        # print current register values
        self.fpga.print_registers()
        self.fpga.get_timing()

        if self.sensor1_on == True:
            self.write_to_file(0)
        if self.sensor2_on == True:
            self.write_to_file(1)
        if self.sensor3_on == True:
            self.write_to_file(2)

    def write_to_file(self, sensorId):
        logger.info("Func() : " + sys._getframe().f_code.co_name)

        # set starting read address 
        offset = 0
        if sensorId == 1:
            offset = SENSOR2_WRITE_BUFFER_ADDRESS
        elif sensorId == 2:
            offset = SENSOR3_WRITE_BUFFER_ADDRESS

        rc = self.fpga.set_register(rMemAddr, offset)
        if rc != ErrorCode.NoError:
            self.exit_app("setting starting read address rc=" + str(rc))

        # set memory read enable
        rc = self.fpga.set_register(rMemRd, 1)
        if rc != ErrorCode.NoError:
            self.exit_app("setting memory read enable rc=" + str(rc))

        # read from the pipe with a multiple of 1024 bytes.
        rc = self.fpga.read_memory(self.buf)
        if rc != ErrorCode.NoError:
            self.exit_app("read memory failed rc=" + str(rc))

        # turn off memory read enable
        rc = self.fpga.set_register(rMemRd, 0)
        if rc != ErrorCode.NoError:
            self.exit_app("setting memory read enable rc=" + str(rc))

        # get memory read count 
        rc, val = self.fpga.get_register(rMemRdCount)
        if rc != ErrorCode.NoError:
            self.exit_app("getting memroy read count rc=" + str(rc))
        else:
            logger.info("Memory read count = " + str(val))

        # write raw data to a file
        if self.raw == True:
            if (sensorId == 0):
                sensor = self.sensor1
            elif(sensorId == 1):
                sensor = self.sensor2
            else:
                sensor = self.sensor3 
            logger.info(str(datetime.now()))
            file_name_raw = IMAGE_SAVE_PATH + str(sensorId+1) + "/sensor" + str(sensorId+1) + "_" + self.timeStamp + ".raw"
            if (self.filename != ""):
                file_name_raw = self.CalFilename(sensorId)
            f = open(file_name_raw, "wb")
            f.write(self.buf)
            f.close()
    
            # write image description to tiff file
            self.make_tag(sensorId)
            tagFile = file_name_raw + TIFFTAG_FILE_EXT 
            self.tag.flush_to_file(tagFile)

        # write to a file
        if self.tiff == True:
            logger.info(str(datetime.now()))
            self.cLib.save_as_16bit(self.buf, self.buf_16bit, self.bufSize)
            #================================================================================== FLIGHT TEST ONLY====================
            #dstFile = IMAGE_SAVE_PATH + str(sensorId+1) + "/sensor" + str(sensorId+1) + "_" + self.timeStamp + ".raw"
            #with open(dstFile, 'wb') as output:
            #    output.write(self.buf)
            #=======================================================================================================================
            logger.info(str(datetime.now()))
            file_name_16bit = IMAGE_SAVE_PATH + RAW_DATA_FILENAME + "_16bit"
            f = open(file_name_16bit, "wb")
            f.write(self.buf_16bit)
            f.close()
            self.fpga.get_temperature()
            if self.writetiff == True:
                   self.convert_to_16bit_tiff(sensorId, file_name_16bit)

        if self.thumbnail == True:
            self.make_thumbnail(sensorId)

    def CalFilename(self, sensorId):
        if (sensorId == 0):
            sensor = self.sensor1
        elif(sensorId == 1):
            sensor = self.sensor2
        else:
            sensor = self.sensor3          
        exposure = "_E" + str(sensor.get_exposure()) + "_G" + str(sensor.get_gain())
        filename = str(exposure) + "_" + str(self.filename)
        file_name_raw = IMAGE_SAVE_PATH + str(sensorId+1) + "/sensor" + str(sensorId+1) + filename + ".raw"
        return file_name_raw

    def serdes(self):
        logger.info("Func() : " + sys._getframe().f_code.co_name)
        
        if (self.sensors == 0):
            print("Warning, serdes NOT running, turn on sensors")
            
        if (self.sensor1_on == True):        
            self.sensor1.set_adc_test_pattern(0x003, True)
            self.fpga.set_register(rManBitSlipS1, 1)
            self.fpga.train(0)
            self.fpga.set_register(rManBitSlipS1, 0)
            self.sensor1.set_adc_test_pattern(0x003, False)

        if (self.sensor2_on == True):
            self.sensor2.set_adc_test_pattern(0x003, True)
            self.fpga.set_register(rManBitSlipS2, 1)
            self.fpga.train(1)
            self.fpga.set_register(rManBitSlipS2, 0)
            self.sensor2.set_adc_test_pattern(0x003, False)

        if (self.sensor3_on == True):
            self.sensor3.set_adc_test_pattern(0x003, True)
            self.fpga.set_register(rManBitSlipS3, 1)
            self.fpga.train(2)
            self.fpga.set_register(rManBitSlipS3, 0)
            self.sensor3.set_adc_test_pattern(0x003, False)        

		
        '''
        # save as 8 bit and write to file
        logger.info(str(datetime.now()))
        self.cLib.save_as_8bit(self.buf, self.buf_8bit, self.bufSize)
        logger.info(str(datetime.now()))
        file_name_8bit = RAW_DATA_FILENAME + "_8bit"
        f = open(file_name_8bit, "wb")
        f.write(self.buf_8bit)
        f.close()
        logger.info(str(datetime.now()))
        self.convert_to_8bit_tiff(sensorId, file_name_8bit)
        '''

    def __del__(self):
        self.gpsp.running = False
        self.gpsp.join()

def main(argsinput, app):

    parser = argparse.ArgumentParser(description="Imager application")

    parser.add_argument("-lval", "--lval", type=str, default="0x09", help="set the lval delay")

    args = parser.parse_args(argsinput)

    app.sensor1.set_delay_lval(args.lval)    #DN added
    print "Get from sensor 1" + str(app.sensor1.get_register(17))
    app.sensor2.set_delay_lval(args.lval)	#DN added
    print "Get from sensor 2" + str(app.sensor2.get_register(17))
    app.sensor3.set_delay_lval(args.lval)    #DN added    
    print "Get from sensor 3" + str(app.sensor3.get_register(17))

if __name__ == "__main__":
    app = Imager(False, 0x7, 0)
    main(sys.argv[1:], app)

