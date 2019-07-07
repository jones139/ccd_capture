#
# ccd_capture.py
# Provides a web based front end to a CCD camera, that is controlled
# using the INDI protocol.

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
        print("IndiClient.newMessage: ",m.real)
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
    
    indiConnected = False
    cameraInitialised = False
    exposureTime = 0.5  # Exposure time in seconds
    subFrameOriginX = 0  # Pixels
    subFrameOriginY = 0  # Pixels
    subFrameSizeX = 0  # Pixels
    subFrameSizeY = 0  # Pixels
    frameSizeX = 0  # Pixels
    frameSizeY = 0  # Pixels
    coolerSetpoint = 0.0 # degC
    coolerOn = False

    curImageTime = 0  # Time current image was collected

    status = STATUS_NO_IMAGE
    errorState = 0  # 0=ok, -1=warning, -2=error
    msg = ""
    
    def __init__(self, cameraId="Atik 383L", dataDir = "."):
        print("ccd_capture.__init__()")
        WebControlClass.__init__(self,portNo=8081)

        self.cameraId = cameraId
        self.dataDir = dataDir
        self.status = self.STATUS_NO_IMAGE

        if (not os.path.exists(self.dataDir)):
            os.makedirs(self.dataDir)
        self.connectINDI(cameraId)
        
        self.startServer()

    def toJson(self):
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
        obj['frameSizeX']=self.frameSizeX
        obj['frameSizeY']=self.frameSizeY
        obj['coolerSetpoint']=self.coolerSetpoint
        obj['coolerOn']=self.coolerOn
        obj['curImageTime']=self.curImageTime


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




    def connectINDI(self, cameraId="Atik 383L"):
        self.indiclient=IndiClient(self.receiveImage)
        self.indiclient.setServer("localhost",7624)

        if (not(self.indiclient.connectServer())):
            self.msg = "No indiserver running on "+ \
                   self.indiclient.getHost()+":"+ \
                   str(self.indiclient.getPort())+ \
                   " - Try to run indiserver -vv indi_atik_ccd" 
            print(self.msg)
            self.errorState = -2
            return
        else:
            print("Server Connected OK")

        if (cameraId == "CCD Simulator"):
            print("Using CCD Simulator, so enabling telescope simulator too")
            self.initialiseTelescopeSimulator()
            
        print("Looking for device %s...." % cameraId)
        self.device_ccd=self.indiclient.getDevice(cameraId)
        print("returned from getDevice")
        while not(self.device_ccd):
            time.sleep(0.5)
            self.device_ccd=self.indiclient.getDevice(cameraId)
            sys.stderr.write(".")
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
        print("got exposure object ", self.ccd_exposure)


        # we should inform the indi server that we want to receive the
        # "CCD1" blob from this device
        print("Setting BLOB Mode")
        self.indiclient.setBLOBMode(PyIndi.B_ALSO, cameraId, "CCD1")

        self.indiConnected = True;

        self.msg = "ConnectINDI Complete"
        self.errorState = 0
        print(self.msg)


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


    def receiveImage_file(self):
        """ called by indiClient when Blob received
        """
        print("receiveImage()")
        for blob in self.ccd_ccd1:
            #print("name: ", blob.name," size: ", blob.size," format: ", blob.format)
            fits=blob.getblobdata()
            #print("fits data type: ", type(fits))

        i=0
        fname="/tmp"
        fpath = fname
        while os.path.exists(fpath):
            i=i+1
            fname = "image%09d.fits" % i
            fpath = os.path.join(self.dataDir, fname)
        ofile = open(fpath, "wb")
        ofile.write(fits)
        ofile.close()
        print("written to file %s" % fname)
        hdulist = astropy.io.fits.open(fpath)
        #print(hdulist.info())
        hdu = hdulist[0]
        #print(hdu.data.shape)
        #print(hdu.header)
        self.curImg = np.asarray(hdu.data,dtype=np.uint16)
        self.status = self.STATUS_IDLE

    def receiveImage(self):
        """ called by indiClient when Blob received
        Memory based file handling from https://www.indilib.org/forum/general/606-take-image-with-python-script/3189.html?start=12
        """
        print("receiveImage()")
        for blob in self.ccd_ccd1:
            #print("name: ", blob.name," size: ", blob.size," format: ", blob.format)
            fits=blob.getblobdata()
            #print("fits data type: ", type(fits))

        i=0
        fname="/tmp"
        fpath = fname
        while os.path.exists(fpath):
            i=i+1
            fname = "image%09d.fits" % i
            fpath = os.path.join(self.dataDir, fname)
        ofile = open(fpath, "wb")
        ofile.write(fits)
        ofile.close()
        print("written to file %s" % fname)

        blobFile = io.BytesIO(fits)
        hdulist = astropy.io.fits.open(blobFile)
        #print(hdulist.info())
        hdu = hdulist[0]
        #print(hdu.data.shape)
        #print(hdu.header)
        self.curImg = np.asarray(hdu.data,dtype=np.uint16)
        self.curImageTime = datetime.now().timestamp()
        self.status = self.STATUS_IDLE
        print("curImageTime=%s" % self.curImageTime)
        

    def getWebImage(self):
        """ return a copy of the current image, scaled to 800 px width
        """
        return self.curImg

    def onWwwCmd(self,cmdStr,valStr, methodStr,request):
        ''' Process the command, with parameter 'valStr' using request
        method methodStr, and return the appropriate response.
        request is the bottlepy request associated with the command
        '''
        print("CcdCapture.onWwwCmd(%s/%s %s)" % (cmdStr,valStr,methodStr))

        if (methodStr=="GET"):
            if (cmdStr.lower()=="getData".lower()):
                return self.toJson()
            if (cmdStr.lower()=="getImage".lower()):
                if (self.status == self.STATUS_NO_IMAGE):
                    print("getImage(): no image yet!")
                    return("<p>No Image</p>")
                else:
                    response.set_header('Content-type', 'image/png')
                    return(self.getWebImage)
            if (cmdStr.lower()=="getFullImage".lower()):
                print("FIXME - Implement getFullImage")
            else:
                print("ERROR - Unreconised Command %s" % cmdStr)
                return("<h1>ERROR - Unreconised Command %s</h1>" % cmdStr)
        elif (methodStr=="POST"):
            if (cmdStr.lower()=="startExposure".lower()):
                print("FIXME - Implement startExposure")
                self.startExposure()
                pass
            elif (cmdStr.lower()=="startContinuousExposures".lower()):
                print("FIXME - Implement startContinuousExposures")
                pass
            elif (cmdStr.lower()=="stopContinuousExposures".lower()):
                print("FIXME - Implement stopContinuousExposures")
                pass
            elif (cmdStr.lower()=="setExposureTime".lower()):
                self.exposureTime = float(valStr)
                return("ok")
            elif (cmdStr.lower()=="setCooler".lower()):
                self.coolerSetpoint = float(valStr)
                self.coolerOn = True
                return("ok")
            elif (cmdStr.lower()=="setSubFrame".lower()):
                origin, size =  valStr.split(":")
                print(origin,size)
                self.subFrameOriginX, self.subFrameOriginY = origin.split(",")
                self.subFrameSizeX, self.subFrameSizeY = size.split(",")
                return("ok")
            else:                
                print("ERROR - Unreconised Command %s" % cmdStr)
                return("<h1>ERROR - Unreconised Command %s</h1>" % cmdStr)
        else:
            print("LSMControl.onWwwCmd - Unsupported Method type, %s." % methodStr)
            return('ERROR - Unsupported Method Type %s' % methodStr)
        
        return('<h1>LSMControl.onWwwCmd - FIXME</h1>'
               'We should not see this message!!!'
               '<br/>cmdStr=%s/%s, method=%s' % (cmdStr,valStr,methodStr))



if __name__ == "__main__":
    print("ccd_capture.__main__()")

    dataDir = "./data"
    cameraId = "CCD Simulator"
    ccdCapture = Ccd_capture(cameraId, dataDir)
    print("Ccd_capture complete")
