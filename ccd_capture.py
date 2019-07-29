#!/usr/bin/env python
#
# ccd_capture.py
#
# MIT License - CCD_CAPTURE
#
# Copyright (c) 2019 Graham Jones
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# 
''' Provides a web based front end to a CCD camera, that is controlled
 using the INDI protocol.

        The following commands are recognised:
        HTTP GET Commands:
        /getData - returns a JSON string summarising the current state.
        /getImage - returns a web-scaled version of the latest camera image.
        /getRoiImage - as for /getImage but the defined ROI is highlighted on the image.
        /getFullImage - NOT IMPLEMENTED
        /getFrameHistogram - returns an image of the pixel intensity histogram for the current image.
        /getRoiHistogram - returns an image of the pixel intensity histogram for the Region of Interest in the current image.
        /getXProfile - returns an image of a graph showing the intensity of pixels across the X direction at the midpoint of the image in Y.
        /getRoiXProfile - returns an image of a graph showing the intensity of pixels across the X direction of the region of interest at the midpoint of the image in Y.
        /getYProfile - returns an image of a graph showing the intensity of pixels across the Y direction at the midpoint of the image in X.
        /getYProfile - returns an image of a graph showing the intensity of pixels across the Y direction of the region of interest at the midpoint of the image in X.

        HTTP POST Commands:
        /startExposure - start a single camera exposure
        /startContinuousExposures - start collecting repeated camera exposures.
        /stopContinuousExposures - stop collecting repeated exposures when the current one completes.
        /saveImage/<fname> - save the current image with the specified filename root.
        /startAutoSave/<fname> - start auto saving every image that is received with the specified filename root.
        /stopAutoSave - stop auto saving images.
        /setExposureTime/<time_secs> - set the camera exposure time to the given time in seconds.
        /setCooler/<setpoint> - set the cooler setpoint to the given value (in degC)
        /setSubFrame/<OriginX>,<OriginY>:<SizeX>,<SizeY> define the subframe in camera pixel coordinates.
        /setRoi/<OriginX>,<OriginY>:<SizeX>,<SizeY> define the ROI in camera pixel coordinates, relative to subFrame origin.
        /clearRoi - resets the ROI back to the whole subframe.

'''

import argparse
from datetime import datetime
import time
import os
import sys
import threading
import json
import numpy as np
import io
import astropy.io.fits
import PyIndi
import cv2
import matplotlib.pyplot as plt
from WebControlClass import WebControlClass


class IndiClient(PyIndi.BaseClient):
    def __init__(self,imgCallback = None):
        super(IndiClient, self).__init__()
        #self.blobEvent=threading.Event()
        #self.blobEvent.clear()
        self.imgCallback = imgCallback

    def newDevice(self, d):
        print("newDevice:",d.getDeviceName())

    def newProperty(self, p):
        #print("New property ", p.getName(), " for device ",
        #      p.getDeviceName())
        #if (p.getName() == "CCD_FRAME"):
        #    for n in p.getNumber():
        #        print(n.name, " = ", n.value)
        pass
    
    def removeProperty(self, p):
        pass
    def newBLOB(self, bp):
        #global blobEvent
        print("new BLOB ", bp.name)
        #self.blobEvent.set()
        #blobEvent.set()
        self.imgCallback()

    def newSwitch(self, svp):
        pass
    def newNumber(self, nvp):
        pass
    def newText(self, tvp):
        print("IndiClient.newText: ",tvp)
        pass
    def newLight(self, lvp):
        pass
    def newMessage(self, d, m):
        #print("IndiClient.newMessage: ",m.real)
        pass
    def serverConnected(self):
        print("serverConnected")




class Ccd_capture(WebControlClass):
    ''' 
    Provide a web interface to a ccd camera using the INDI protocol.
    '''
    STATUS_ERROR = -1
    STATUS_NO_IMAGE = 0
    STATUS_IDLE = 1
    STATUS_EXPOSING = 2
    STATUS_DOWNLOADING = 3

    WEB_X_MAX = 600
    WEB_Y_MAX = 400
    
    indiConnected = False
    cameraInitialised = False
    exposureTime = 0.5  # Exposure time in seconds
    subFrameOriginX = 0  # Pixels
    subFrameOriginY = 0  # Pixels
    subFrameSizeX = 500  # Pixels
    subFrameSizeY = 500  # Pixels
    roiOriginX = 0  # Pixels
    roiOriginY = 0  # Pixels
    roiSizeX = 100  # Pixels
    roiSizeY = 100  # Pixels
    frameSizeX = 0  # Pixels
    frameSizeY = 0  # Pixels
    coolerSetpoint = 0.0 # degC
    coolerOn = False
    ccdTemp = -1
    continuousMode = False
    saveFnameRoot = "fname"
    autoSave = False

    curImageTime = 0  # Time current image was collected

    curImageMean = -1
    curImageSd = -1
    curRoiMean = -1
    curRoiSd = -1

    status = STATUS_NO_IMAGE
    errorState = 0  # 0=ok, -1=warning, -2=error
    msg = ""
    
    def __init__(self, cameraId="Atik 383L", dataDir = "."):
        print("ccd_capture.__init__()")
        WebControlClass.__init__(self,portNo=8081)

        self.cameraId = cameraId
        self.dataDir = os.path.join(self.wwwPath,dataDir)
        print("dataDir=%s" % self.dataDir)
        self.status = self.STATUS_NO_IMAGE

        if (not os.path.exists(self.dataDir)):
            os.makedirs(self.dataDir)
        self.connectINDI(cameraId)
        
        self.startServer()

    def toJson(self):
        """ Returns a JSON representation of the current ccd status """
        self.getCcdTemperature()
        
        obj = {}
        obj['statusVal']=self.status
        obj['errorState']=self.errorState
        obj['msg']=self.msg
        obj['cameraId']=self.cameraId
        obj['exposureTime']=self.exposureTime
        obj['subFrameOriginX']=self.subFrameOriginX
        obj['subFrameOriginY']=self.subFrameOriginY
        obj['subFrameSizeX']=self.subFrameSizeX
        obj['subFrameSizeY']=self.subFrameSizeY
        obj['roiOriginX']=self.roiOriginX
        obj['roiOriginY']=self.roiOriginY
        obj['roiSizeX']=self.roiSizeX
        obj['roiSizeY']=self.roiSizeY
        obj['frameSizeX']=self.frameSizeX
        obj['frameSizeY']=self.frameSizeY
        obj['coolerSetpoint']=self.coolerSetpoint
        obj['coolerOn']=self.coolerOn
        obj['ccdTemp']=self.ccdTemp
        obj['curImageTime']=self.curImageTime
        obj['curImageMean']="%.1f" % self.curImageMean
        obj['curImageSd']="%.1f" % self.curImageSd
        obj['curRoiMean']="%.1f" % self.curRoiMean
        obj['curRoiSd']="%.1f" % self.curRoiSd


        jsonStr = json.dumps(obj,indent=2,sort_keys=True)
        #print jsonStr
        return jsonStr


    def initialiseCamera(self):
        """ Query the INDI Server to get the current camera settings.
        Sets the sub frame to be the full frame.
        """
        pass


    def initialiseTelescopeSimulator(self):
        # connect the scope
        telescope="Telescope Simulator"
        device_telescope=None
        telescope_connect=None

        # get the telescope device
        device_telescope=self.indiclient.getDevice(telescope)
        while not(device_telescope):
            time.sleep(0.5)
            device_telescope=self.indiclient.getDevice(telescope)
            
        # wait CONNECTION property be defined for telescope
        telescope_connect=device_telescope.getSwitch("CONNECTION")
        while not(telescope_connect):
            time.sleep(0.5)
            telescope_connect=device_telescope.getSwitch("CONNECTION")

        # if the telescope device is not connected, we do connect it
        if not(device_telescope.isConnected()):
            # Property vectors are mapped to iterable Python objects
            # Hence we can access each element of the vector using Python indexing
            # each element of the "CONNECTION" vector is a ISwitch
            telescope_connect[0].s=PyIndi.ISS_ON  # the "CONNECT" switch
            telescope_connect[1].s=PyIndi.ISS_OFF # the "DISCONNECT" switch
            self.indiclient.sendNewSwitch(telescope_connect) # send this new value to the device
                
        # Now let's make a goto to vega
        # Beware that ra/dec are in decimal hours/degrees
        vega={'ra': (279.23473479 * 24.0)/360.0, 'dec': +38.78368896 }

        # We want to set the ON_COORD_SET switch to engage tracking after goto
        # device.getSwitch is a helper to retrieve a property vector
        telescope_on_coord_set=device_telescope.getSwitch("ON_COORD_SET")
        while not(telescope_on_coord_set):
            time.sleep(0.5)
            telescope_on_coord_set=device_telescope.getSwitch("ON_COORD_SET")
        # the order below is defined in the property vector, look at the standard Properties page
        # or enumerate them in the Python shell when you're developing your program
        telescope_on_coord_set[0].s=PyIndi.ISS_ON  # TRACK
        telescope_on_coord_set[1].s=PyIndi.ISS_OFF # SLEW
        telescope_on_coord_set[2].s=PyIndi.ISS_OFF # SYNC
        self.indiclient.sendNewSwitch(telescope_on_coord_set)
        # We set the desired coordinates
        telescope_radec=device_telescope.getNumber("EQUATORIAL_EOD_COORD")
        while not(telescope_radec):
            time.sleep(0.5)
            telescope_radec=device_telescope.getNumber("EQUATORIAL_EOD_COORD")
        telescope_radec[0].value=vega['ra']
        telescope_radec[1].value=vega['dec']
        self.indiclient.sendNewNumber(telescope_radec)
        # and wait for the scope has finished moving
        while (telescope_radec.s==PyIndi.IPS_BUSY):
            print("Scope Moving ", telescope_radec[0].value, telescope_radec[1].value)
            time.sleep(2)




    def connectINDI(self,
                    cameraId="Atik 383L",
                    serverHost = "localhost",
                    serverPort = 7624):
        self.indiclient=IndiClient(self.receiveImage)
        self.indiclient.setServer(serverHost, serverPort)

        if (not(self.indiclient.connectServer())):
            self.msg = "\n************************************************\n" + \
                       " ERROR: No indiserver running on "+ \
                   self.indiclient.getHost()+":"+ \
                   str(self.indiclient.getPort())+ \
                   "\n - Try running indiserver -vv indi_atik_ccd" + \
                   "\n -   or indiserver -vv indi_simulator_ccd indi_simulator_telescope" + \
                   "\n************************************************\n"
            print(self.msg)
            self.errorState = -2
            exit(-1)
        else:
            print("Server Connected OK")

        if (cameraId == "CCD Simulator"):
            print("Using CCD Simulator, so enabling telescope simulator too")
            self.initialiseTelescopeSimulator()
            
        print("Looking for device %s...." % cameraId)
        self.device_ccd=self.indiclient.getDevice(cameraId)
        nRetries = 0
        while not(self.device_ccd):
            time.sleep(0.5)
            self.device_ccd=self.indiclient.getDevice(cameraId)
            sys.stderr.write(".")
            sys.stderr.flush()
            nRetries += 1

            if (nRetries >= 20):
                print("")
                print("")
                print("***********************************************")
                print("ERROR - Failed to find Device %s" % cameraId)
                print(" - Check that the INDI server is providing it")
                print("***********************************************")
                exit(-1)
        print("\nFound device!")

        print("Connecting to Device")
        self.ccd_connect=self.device_ccd.getSwitch("CONNECTION")
        while not(self.ccd_connect):
            time.sleep(0.5)
            self.ccd_connect=self.device_ccd.getSwitch("CONNECTION")
            sys.stderr.write(".")
        print("\nConnected!")
        if not(self.device_ccd.isConnected()):
            print("oh no - isConnected is false - fiddling...")
            self.ccd_connect[0].s=PyIndi.ISS_ON  # the "CONNECT" switch
            self.ccd_connect[1].s=PyIndi.ISS_OFF # the "DISCONNECT" switch
            self.indiclient.sendNewSwitch(self.ccd_connect)

        print("Getting Exposure Object..")
        self.ccd_exposure=self.device_ccd.getNumber("CCD_EXPOSURE")
        while not(self.ccd_exposure):
            time.sleep(0.5)
            self.ccd_exposure=self.device_ccd.getNumber("CCD_EXPOSURE")
            sys.stderr.write(".")
        print("got exposure object ")

        self.getFrame()
        self.getSubFrame()
        
        # we should inform the indi server that we want to receive the
        # "CCD1" blob from this device
        print("Setting BLOB Mode")
        self.indiclient.setBLOBMode(PyIndi.B_ALSO, cameraId, "CCD1")

        self.indiConnected = True;

        self.msg = "ConnectINDI Complete"
        self.errorState = 0
        print(self.msg)


    def getFrame(self):
        """ Populates this object with the current frame dimensions
        in the camera.
        """
        print("Getting CCD_INFO Object..")
        ccd_info=self.device_ccd.getNumber("CCD_INFO")
        while not(ccd_info):
            time.sleep(0.5)
            ccd_info=self.device_ccd.getNumber("CCD_INFO")
            sys.stderr.write(".")
            sys.stderr.flush()
        print("got ccd_info object: ")
        for n in ccd_info:
            print(n.name," = ",n.value)
        self.frameSizeX = ccd_info[0].value
        self.frameSizeY = ccd_info[1].value
        print("getFrame Complete")

    def getSubFrame(self):
        """ Populates this object with the current subframe dimensions
        in the camera.
        """
        print("Getting Frame Object..")
        ccd_frame=self.device_ccd.getNumber("CCD_FRAME")
        while not(ccd_frame):
            time.sleep(0.5)
            ccd_frame=self.device_ccd.getNumber("CCD_FRAME")
            sys.stderr.write(".")
        print("got frame object:")
        for n in ccd_frame:
            print(n.name," = ",n.value)
        self.subFrameOriginX = int(ccd_frame[0].value)
        self.subFrameOriginY = int(ccd_frame[1].value)
        self.subFrameSizeX = int(ccd_frame[2].value)
        self.subFrameSizeY = int(ccd_frame[3].value)
        print("getSubFrame complete")

    def setSubFrame(self):
        """ sets the camera frame dimensions based on the properties
        of this object.
        """
        print("Getting Frame Object..")
        ccd_frame=self.device_ccd.getNumber("CCD_FRAME")
        while not(ccd_frame):
            time.sleep(0.5)
            ccd_frame=self.device_ccd.getNumber("CCD_FRAME")
            sys.stderr.write(".")
        print("got frame object ", ccd_frame)
        for n in ccd_frame:
            print(n.name," = ",n.value)
        ccd_frame[0].value = self.subFrameOriginX
        ccd_frame[1].value = self.subFrameOriginY
        ccd_frame[2].value = self.subFrameSizeX
        ccd_frame[3].value = self.subFrameSizeY
        self.indiclient.sendNewNumber(ccd_frame)
        print("setFrame complete")

    def clearSubFrame(self):
        """ Reset the camera subframe to be the whole sensor dimensions.
        """
        self.subFrameOriginX = 0
        self.subFrameOriginY = 0
        self.subFrameSizeX = self.frameSizeX
        self.subFrameSizeY = self.frameSizeY
        self.setSubFrame()
        print("clearSubFrame complete")


        
    def getCcdTemperature(self):
        """ Retrieve the current temperature of the CCD from the camera
        """
        #print("Getting CCD Temperature..")
        ccd_temp=self.device_ccd.getNumber("CCD_TEMPERATURE")
        while not(ccd_temp):
            time.sleep(0.5)
            ccd_frame=self.device_ccd.getNumber("CCD_TEMPERATURE")
            sys.stderr.write(".")
            sys.stderr.flush()
        #print("got ccd_temp object ", ccd_temp)
        #for n in ccd_temp:
        #    print(n.name," = ",n.value)
        self.ccdTemp = ccd_temp[0].value

        #print("getCcdTemperature complete")

    def setCooler(self,startCooler = True):
        """ Sets up the cooler.  if startCooler is true, the cooler
        is switched on with setpoint self.coolerSetpoint.
        if startCooler is False, the cooler is switched off.
        """
        #print("Getting CCD Temperature..")
        ccd_temp=self.device_ccd.getNumber("CCD_TEMPERATURE")
        while not(ccd_temp):
            time.sleep(0.5)
            ccd_frame=self.device_ccd.getNumber("CCD_TEMPERATURE")
            sys.stderr.write(".")
            sys.stderr.flush()
        #print("got ccd_temp object ", ccd_temp)
        #for n in ccd_temp:
        #    print(n.name," = ",n.value)
        ccd_temp[0].value = self.coolerSetpoint
        self.indiclient.sendNewNumber(ccd_temp)

        #print("getCcdTemperature complete")
        #print("Getting Cooler Object..")
        #ccd_cooler=self.device_ccd.getNumber("CCD_COOLER")
        #while not(ccd_cooler):
        #    time.sleep(0.5)
        #    ccd_cooler=self.device_ccd.getNumber("CCD_COOLER")
        #    sys.stderr.write(".")
        #    sys.stderr.flush()
        #print("got cooler object ", ccd_cooler)
        #for n in ccd_cooler:
        #    print(n.name," = ",n.value)
        #ccd_cooler[0].value = self.coolerSetpoint
        #if (startCooler == True):
        #    ccd_cooler[1].value = 1
        #    self.coolerOn = True
        #else:
        #    ccd_cooler[1].value = 0
        #    self.coolerOn = False
        #self.indiclient.sendNewNumber(ccd_cooler)
        print("setCooler complete")

        
        
    def startExposure(self):
        """ Request the camera to start an exposure """
        print("startExposure()")
        if not self.indiConnected:
            self.connectINDI()

        print("Getting Blob")
        self.ccd_ccd1=self.device_ccd.getBLOB("CCD1")
        while not(self.ccd_ccd1):
            time.sleep(0.5)
            self.ccd_ccd1=self.device_ccd.getBLOB("CCD1")
            sys.stderr.write(".")

        print("got Blob")

        #self.indiclient.blobEvent.clear()
        # global blobEvent
        # blobEvent=threading.Event()
        # blobEvent.clear()
        
        print("Sending exposure object...")
        self.status = self.STATUS_EXPOSING
        self.ccd_exposure[0].value=self.exposureTime
        #print("Setting exposure to %s" % self.ccd_exposure[0])
        self.indiclient.sendNewNumber(self.ccd_exposure)
        #print("waiting for Image Data....")
        #blobEvent.wait()

        print("startExposure Complete")



    def receiveImage(self):
        """ called by indiClient when Blob received
        Memory based file handling from https://www.indilib.org/forum/general/606-take-image-with-python-script/3189.html?start=12
        """
        print("receiveImage()")
        for blob in self.ccd_ccd1:
            #print("name: ", blob.name," size: ", blob.size," format: ", blob.format)
            fits=blob.getblobdata()
            #print("fits data type: ", type(fits))

        # i=0
        #fname="/tmp"
        #fpath = fname
        #while os.path.exists(fpath):
        #    i=i+1
        #    fname = "image%09d.fits" % i
        #    fpath = os.path.join(self.dataDir, fname)
        #ofile = open(fpath, "wb")
        #ofile.write(fits)
        #ofile.close()
        #print("written to file %s" % fname)

        blobFile = io.BytesIO(fits)
        hdulist = astropy.io.fits.open(blobFile)
        #print(hdulist.info())
        hdu = hdulist[0]
        #print(hdu.data.shape)
        #print(hdu.header)
        self.curImg = np.asarray(hdu.data,dtype=np.uint16)
        self.curImageTime = datetime.now().timestamp()
        self.curImageMean = self.curImg.mean()
        self.curImageSd = 100 * self.curImg.std() / self.curImageMean

        roiImg = self.curImg[self.roiOriginY :
                             self.roiOriginY + self.roiSizeY,
                             self.roiOriginX :
                             self.roiOriginX + self.roiSizeX]

        self.curRoiMean = roiImg.mean()
        self.curRoiSd = 100 * roiImg.std() / self.curRoiMean
        self.status = self.STATUS_IDLE
        print("curImageTime=%s" % self.curImageTime)

        if (self.autoSave):
            self.saveImage()

        if (self.continuousMode):
            self.startExposure()
        

    def saveImage(self):
        """ Save the current image to disk using the base filename
        fnameRoot.  The image date/time is also appended to the filename
        with a further index number if necesssary to ensure it is unique.
        """
        i=0
        imgDt = datetime.fromtimestamp(self.curImageTime)
        tsStr = imgDt.strftime("%Y%m%d%H%M%S")
        fname="%s-%s-%03d.tif" % (self.saveFnameRoot,tsStr,i)
        fpath = os.path.join(self.dataDir, fname)
        while os.path.exists(fpath):
            i=i+1
            fname="%s-%s-%03d.tif" % (self.saveFnameRoot,tsStr,i)
            fpath = os.path.join(self.dataDir, fname)
        print("saveImg - Saving to %s.  dataDir=%s" % (fpath,self.dataDir))

        cv2.imwrite(fpath,self.curImg)
        return("ok")
        
        
    def resizeImgForWeb(self,img):
        """ Returns a re-sized image for web viewing """
        xMax = int(self.WEB_X_MAX)
        yMax = int(img.shape[0] * xMax / img.shape[1])

        if (yMax > self.WEB_Y_MAX):
            yMax = int(self.WEB_Y_MAX)
            xMax = int(img.shape[1] * yMax / img.shape[0])
        res = cv2.resize(img, dsize=(xMax,yMax),
                         interpolation=cv2.INTER_CUBIC)
        return(res)

    def getWebImage(self):
        """ return a copy of the current image, scaled to 800 px width
        """
        res = self.resizeImgForWeb(self.curImg)
        success, encImg = cv2.imencode('.png',res)
        imgBytes = encImg.tobytes()
        return(imgBytes)

    def getRoiWebImage(self):
        """ return a copy of the current image, scaled to 800 px width
        """
        roiImg = cv2.cvtColor(self.curImg,cv2.COLOR_GRAY2RGB)
        cv2.rectangle(roiImg,
                      (self.roiOriginX, self.roiOriginY),
                      (self.roiOriginX + self.roiSizeX,
                       self.roiOriginY + self.roiSizeY),
                      (65535,0,0),
                      3)
        res = self.resizeImgForWeb(roiImg)
        success, encImg = cv2.imencode('.png',res)
        imgBytes = encImg.tobytes()
        return(imgBytes)

    
    def getFrameHistogram(self):
        """ get an image of the histogram of the current image.
        """
        histData, bins = np.histogram(self.curImg,256)
        fig, ax = plt.subplots( nrows=1, ncols=1 )  # create figure & 1 axis
        #print(histData)
        ax.plot(histData)
        ax.set_title("Intensity Histogram")
        histImg = io.BytesIO()
        fig.savefig(histImg, format='png')
        histImg.seek(0)
        fig.savefig('hist.png')   # save the figure to file
        plt.close(fig)    # close the figure
        return(histImg)

    def getRoiHistogram(self):
        """ get an image of the histogram of the current image ROI.
        """
        roiImg = self.curImg[self.roiOriginY :
                             self.roiOriginY + self.roiSizeY,
                             self.roiOriginX :
                             self.roiOriginX + self.roiSizeX]
        histData, bins = np.histogram(roiImg,256)
        fig, ax = plt.subplots( nrows=1, ncols=1 )  # create figure & 1 axis
        #print(histData)
        ax.plot(histData)
        ax.set_title("ROI Intensity Histogram")
        histImg = io.BytesIO()
        fig.savefig(histImg, format='png')
        histImg.seek(0)
        fig.savefig('hist.png')   # save the figure to file
        plt.close(fig)    # close the figure
        return(histImg)

    
    def getXProfile(self):
        """ get an image of the X profile chart
        """
        midY = int(self.curImg.shape[0]/2)
        intProfile = self.curImg[midY,:]
        xData = np.linspace(0,self.curImg.shape[1]-1,self.curImg.shape[1])
        fig, ax = plt.subplots( nrows=1, ncols=1 )  # create figure & 1 axis
        #print(xData,intProfile)
        ax.plot(xData,intProfile)
        ax.set_title("X Intensity Profile")
        histImg = io.BytesIO()
        fig.savefig(histImg, format='png')
        histImg.seek(0)
        fig.savefig('xProfile.png')   # save the figure to file
        plt.close(fig)    # close the figure
        return(histImg)

    def getRoiXProfile(self):
        """ get an image of the ROI X profile chart
        """
        roiImg = self.curImg[self.roiOriginY :
                             self.roiOriginY + self.roiSizeY,
                             self.roiOriginX :
                             self.roiOriginX + self.roiSizeX]
        midY = int(roiImg.shape[0]/2)
        intProfile = roiImg[midY,:]
        xData = np.linspace(0,roiImg.shape[1]-1,roiImg.shape[1])
        fig, ax = plt.subplots( nrows=1, ncols=1 )  # create figure & 1 axis
        #print(xData,intProfile)
        ax.plot(xData,intProfile)
        ax.set_title("ROI X Intensity Profile")
        histImg = io.BytesIO()
        fig.savefig(histImg, format='png')
        histImg.seek(0)
        fig.savefig('roiXProfile.png')   # save the figure to file
        plt.close(fig)    # close the figure
        return(histImg)
    
    def getYProfile(self):
        """ get an image of the Y profile chart
        """
        midX = int(self.curImg.shape[1]/2)
        intProfile = self.curImg[:,midX]
        xData = np.linspace(0,self.curImg.shape[0]-1,self.curImg.shape[0])
        fig, ax = plt.subplots( nrows=1, ncols=1 )  # create figure & 1 axis
        #print(xData,intProfile)
        ax.plot(xData,intProfile)
        ax.set_title("Y Intensity Profile")
        histImg = io.BytesIO()
        fig.savefig(histImg, format='png')
        histImg.seek(0)
        fig.savefig('yProfile.png')   # save the figure to file
        plt.close(fig)    # close the figure

        return(histImg)
    
    def getRoiYProfile(self):
        """ get an image of the Y profile chart
        """
        roiImg = self.curImg[self.roiOriginY :
                             self.roiOriginY + self.roiSizeY,
                             self.roiOriginX :
                             self.roiOriginX + self.roiSizeX]
        midX = int(roiImg.shape[1]/2)
        intProfile = roiImg[:,midX]
        xData = np.linspace(0,roiImg.shape[0]-1,roiImg.shape[0])
        fig, ax = plt.subplots( nrows=1, ncols=1 )  # create figure & 1 axis
        #print(xData,intProfile)
        ax.plot(xData,intProfile)
        ax.set_title("ROI Y Intensity Profile")
        histImg = io.BytesIO()
        fig.savefig(histImg, format='png')
        histImg.seek(0)
        fig.savefig('roiYProfile.png')   # save the figure to file
        plt.close(fig)    # close the figure

        return(histImg)
    
        
    def onWwwCmd(self,cmdStr,valStr, methodStr,request):
        ''' Process the command, with parameter 'valStr' using request
        method methodStr, and return the appropriate response.
        request is the bottlepy request associated with the command.
        The following commands are recognised:
        HTTP GET Commands:
        /getData - returns a JSON string summarising the current state.
        /getImage - returns a web-scaled version of the latest camera image.
        /getRoiImage - as for /getImage but the defined ROI is highlighted on the image.
        /getFullImage - NOT IMPLEMENTED
        /getFrameHistogram - returns an image of the pixel intensity histogram for the current image.
        /getRoiHistogram - returns an image of the pixel intensity histogram for the Region of Interest in the current image.
        /getXProfile - returns an image of a graph showing the intensity of pixels across the X direction at the midpoint of the image in Y.
        /getRoiXProfile - returns an image of a graph showing the intensity of pixels across the X direction of the region of interest at the midpoint of the image in Y.
        /getYProfile - returns an image of a graph showing the intensity of pixels across the Y direction at the midpoint of the image in X.
        /getYProfile - returns an image of a graph showing the intensity of pixels across the Y direction of the region of interest at the midpoint of the image in X.

        HTTP POST Commands:
        /startExposure - start a single camera exposure
        /startContinuousExposures - start collecting repeated camera exposures.
        /stopContinuousExposures - stop collecting repeated exposures when the current one completes.
        /saveImage/<fname> - save the current image with the specified filename root.
        /startAutoSave/<fname> - start auto saving every image that is received with the specified filename root.
        /stopAutoSave - stop auto saving images.
        /setExposureTime/<time_secs> - set the camera exposure time to the given time in seconds.
        /setCooler/<setpoint> - set the cooler setpoint to the given value (in degC)
        /setSubFrame/<OriginX>,<OriginY>:<SizeX>,<SizeY> define the subframe in camera pixel coordinates.
        /setRoi/<OriginX>,<OriginY>:<SizeX>,<SizeY> define the ROI in camera pixel coordinates, relative to subFrame origin.
        /clearRoi - resets the ROI back to the whole subframe.

        '''
        print("CcdCapture.onWwwCmd(%s/%s %s)" % (cmdStr,valStr,methodStr))

        if (methodStr=="GET"):
            if (cmdStr.lower()=="getData".lower()):
                return self.toJson()
            elif (cmdStr.lower()=="getImage".lower()):
                if (self.status == self.STATUS_NO_IMAGE):
                    print("getImage(): no image yet!")
                    return("<p>No Image</p>")
                else:
                    # response.set_header('Content-type', 'image/png')
                    img = self.getWebImage()
                    #print("getImage: img=",img)
                    return(img)
            elif (cmdStr.lower()=="getRoiImage".lower()):
                if (self.status == self.STATUS_NO_IMAGE):
                    print("getRoiImage(): no image yet!")
                    return("<p>No Image</p>")
                else:
                    # response.set_header('Content-type', 'image/png')
                    img = self.getRoiWebImage()
                    #print("getRoi Image: img=",img)
                    return(img)
            elif (cmdStr.lower()=="getFullImage".lower()):
                print("FIXME - Implement getFullImage")
            elif (cmdStr.lower()=="getFrameHistogram".lower()):
                if (self.status == self.STATUS_NO_IMAGE):
                    print("getFrameHistogram(): no image yet!")
                    return("<p>No Image</p>")
                else:
                    img = self.getFrameHistogram()
                    return(img)
            elif (cmdStr.lower()=="getXProfile".lower()):
                if (self.status == self.STATUS_NO_IMAGE):
                    print("getXProfile(): no image yet!")
                    return("<p>No Image</p>")
                else:
                    img = self.getXProfile()
                    return(img)
            elif (cmdStr.lower()=="getYProfile".lower()):
                if (self.status == self.STATUS_NO_IMAGE):
                    print("getYProfile(): no image yet!")
                    return("<p>No Image</p>")
                else:
                    img = self.getYProfile()
                    return(img)

            elif (cmdStr.lower()=="getRoiHistogram".lower()):
                if (self.status == self.STATUS_NO_IMAGE):
                    print("getRoiHistogram(): no image yet!")
                    return("<p>No Image</p>")
                else:
                    img = self.getRoiHistogram()
                    return(img)
            elif (cmdStr.lower()=="getRoiXProfile".lower()):
                if (self.status == self.STATUS_NO_IMAGE):
                    print("getRoiXProfile(): no image yet!")
                    return("<p>No Image</p>")
                else:
                    img = self.getRoiXProfile()
                    return(img)
            elif (cmdStr.lower()=="getRoiYProfile".lower()):
                if (self.status == self.STATUS_NO_IMAGE):
                    print("getRoiYProfile(): no image yet!")
                    return("<p>No Image</p>")
                else:
                    img = self.getRoiYProfile()
                    return(img)


            else:
                print("ERROR - Unreconised Command %s" % cmdStr)
                return("<h1>ERROR - Unreconised Command %s</h1>" % cmdStr)
        elif (methodStr=="POST"):
            if (cmdStr.lower()=="startExposure".lower()):
                self.startExposure()
                pass
            elif (cmdStr.lower()=="startContinuousExposures".lower()):
                self.continuousMode = True
                self.startExposure()
                pass
            elif (cmdStr.lower()=="stopContinuousExposures".lower()):
                self.continuousMode = False
                pass
            elif (cmdStr.lower()=="saveImage".lower()):
                self.saveFnameRoot = valStr
                self.saveImage()
                return("ok")
            elif (cmdStr.lower()=="startAutoSave".lower()):
                self.saveFnameRoot = valStr
                self.autoSave = True
                self.saveImage()
                return("ok")
            elif (cmdStr.lower()=="stopAutoSave".lower()):
                self.autoSave = False
                return("ok")
            elif (cmdStr.lower()=="setExposureTime".lower()):
                self.exposureTime = float(valStr)
                return("ok")
            elif (cmdStr.lower()=="setCooler".lower()):
                self.coolerSetpoint = float(valStr)
                self.setCooler(True)
                return("ok")
            elif (cmdStr.lower()=="setSubFrame".lower()):
                origin, size =  valStr.split(":")
                print(origin,size)
                self.subFrameOriginX = int(origin.split(",")[0])
                self.subFrameOriginY = int(origin.split(",")[1])
                self.subFrameSizeX   = int(size.split(",")[0])
                self.subFrameSizeY   = int(size.split(",")[1])
                self.setSubFrame()
                return("ok")
            elif (cmdStr.lower()=="clearSubFrame".lower()):
                self.clearSubFrame()
                return("ok")
            elif (cmdStr.lower()=="setRoi".lower()):
                origin, size =  valStr.split(":")
                print(origin,size)
                self.roiOriginX = int(origin.split(",")[0])
                self.roiOriginY = int(origin.split(",")[1])
                self.roiSizeX   = int(size.split(",")[0])
                self.roiSizeY   = int(size.split(",")[1])

                if (self.roiOriginX + self.roiSizeX > self.subFrameSizeX):
                    self.roiSizeX = self.subFrameSizeX - self.roiOriginX
                    print("Clipped ROI to fit in subFrame - X")
                if (self.roiOriginY + self.roiSizeY > self.subFrameSizeY):
                    self.roiSizeY = self.subFrameSizeY - self.roiOriginY
                    print("Clipped ROI to fit in subFrame - Y")
                return("ok")
            elif (cmdStr.lower()=="clearRoi".lower()):
                self.roiOriginX = int(self.subFrameOriginX)
                self.roiOriginY = int(self.subFrameOriginY)
                self.roiSizeX   = int(self.subFrameSizeX)
                self.roiSizeY   = int(self.subFrameSizeY)
            else:                
                print("ERROR - Unreconised Command %s" % cmdStr)
                return("<h1>ERROR - Unreconised Command %s</h1>" % cmdStr)
        else:
            print("ccd_capture.onWwwCmd - Unsupported Method type, %s." % methodStr)
            return('ERROR - Unsupported Method Type %s' % methodStr)
        
        return('<h1>ccd_capture.onWwwCmd - FIXME</h1>'
               'We should not see this message!!!'
               '<br/>cmdStr=%s/%s, method=%s' % (cmdStr,valStr,methodStr))



if __name__ == "__main__":
    print("ccd_capture.__main__()")


    parser = argparse.ArgumentParser(description='CCD Camera Server')
    parser.add_argument('--sim', dest='simulator', action='store_true',
                        help='Use the simulator rather than the real camera')

    argsNamespace = parser.parse_args()
    args = vars(argsNamespace)
    print(args)

    
    dataDir = "data"
    if (args['simulator']):
        cameraId = "CCD Simulator"
    else:
        cameraId = "Atik 383L"
    ccdCapture = Ccd_capture(cameraId, dataDir)
    print("Ccd_capture complete")
