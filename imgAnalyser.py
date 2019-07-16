#!/usr/bin/env python
#
# imgAnalyser.py
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

'''imgAnalyser - A class to provide some standard analyses of
images.
'''
import io
import os
import numpy as np
import cv2
import matplotlib.pyplot as plt


# ROI indices
X_ORIGIN = 0
Y_ORIGIN = 1
X_SIZE = 2
Y_SIZE = 3

class ImgAnalyser():
    img = None
    imgSizeX = None
    imgSizeY = None
    roi = [0,0,-1,-1]
    xProfileWidth = 1
    yProfileWidth = 1
    
    WEB_X_MAX = 600
    WEB_Y_MAX = 400
    
    def __init__(self, img = None):
        """ Initialise the ImgAnalyser, with image img, which should be a
        numpy array.
        """
        if not img is None:
            self.setImg(img)
        
    def setImg(self,img):
        """ Initialise the image analyser with image img, which should be
        a numpy array or a string.  If it is a string it is interpreted
        as a file path and the image is loaded from that file.
        """
        IMG_EXTS = (".tif", ".TIF",
                    ".png", ".PNG"
        )
        if not isinstance(img,np.ndarray):
            # If we have not been passed an ndarray, treat it as a filename
            # and try to open it.
            if (not os.path.exists(img)):
                print("ERROR - %s does not exist")
                self.img = None
                return(-1)
            else:
                if not img.endswith(IMG_EXTS):
                    print("Unrecognised file extension %s." % img)
                    self.img = None
                    return(-1)
                img = cv2.imread(img,cv2.IMREAD_ANYDEPTH)
                #print("Read Image - depth=",img.dtype)

        self.imgSizeX = img.shape[1]
        self.imgSizeY = img.shape[0]
        self.img = img
        

    def getImgSize(self):
        return((self.imgSizeX, self.imgSizeY))
        
    def str2roi(self,roiStr):
        """ Convert a string ROI representation
        "<xorigin>,<yorigin>:<xsize>,<ysize>" into an ROI tuple
        (xorigin,yorigin,xsize,ysize).
        """
        originStr, sizeStr = roiStr.split(":")
        #print("originStr=",originStr," sizeStr=",sizeStr)
        xOrigin = int(originStr.split(",")[0])
        yOrigin = int(originStr.split(",")[1])
        xSize = int(sizeStr.split(",")[0])
        ySize = int(sizeStr.split(",")[1])
        return((xOrigin, yOrigin, xSize, ySize))


        
    def setRoi(self,roi):
        """ Check and set the ROI dimensions based on ROI, which should
        be an array [X_Origin, Y_Origin, X_Size, Y_Size]
        """
        if (self.img is None):
            print("Error - need to call setImg before setRoi")
            return(-1)

        if ((roi[X_ORIGIN] >= 0) and (roi[X_ORIGIN]<self.imgSizeX)):
            self.roi[X_ORIGIN] = int(roi[X_ORIGIN])
        else:
            print("WARNING: ROI[X_ORIGIN] %d Out of Range - using zero" %
                  roi[X_ORIGIN])
            self.roi[X_ORIGIN] = 0

        if ((roi[Y_ORIGIN] >= 0) and (roi[Y_ORIGIN]<self.imgSizeY)):
            self.roi[Y_ORIGIN] = int(roi[Y_ORIGIN])
        else:
            print("WARNING: ROI[Y_ORIGIN] %d Out of Range - using zero" %
                  roi[Y_ORIGIN])
            self.roi[Y_ORIGIN] = 0

        if ((roi[X_ORIGIN] + roi[X_SIZE]) <= self.imgSizeX):
            self.roi[X_SIZE] = int(roi[X_SIZE])
        else:
            self.roi[X_SIZE] = self.imgSizeX - self.roi[X_ORIGIN]
            print("WARNING: ROI[X_SIZE] %d Out of Range - using %d" %
                  (roi[X_SIZE], self.roi[X_SIZE]))

        if ((roi[Y_ORIGIN] + roi[Y_SIZE]) <= self.imgSizeY):
            self.roi[Y_SIZE] = int(roi[Y_SIZE])
        else:
            self.roi[Y_SIZE] = self.imgSizeY - self.roi[Y_ORIGIN]
            print("WARNING: ROI[Y_SIZE] %d Out of Range - using %d" %
                  (roi[Y_SIZE], self.roi[Y_SIZE]))

        self.setProfiles(self.xProfileWidth, self.yProfileWidth)
            

    def setProfiles(self,xProfileWidth = 1, yProfileWidth = 1):
        """ Initialise the X and Y profile parameters required to achieve
        the specified profile widths.
        """
        if (xProfileWidth > self.roi[X_SIZE]):
            print("WARNING: Truncating profile width to ROI size")
            xProfileWidth = self.roi[X_SIZE]
        if (yProfileWidth > self.roi[Y_SIZE]):
            print("WARNING: Truncating profile width to ROI size")
            yProfileWidth = self.roi[Y_SIZE]
        
        xProfileMid = self.roi[X_ORIGIN] + (self.roi[X_SIZE])/2.
        yProfileMid = self.roi[Y_ORIGIN] + (self.roi[Y_SIZE])/2.

        self.xProfileMin = int(xProfileMid - xProfileWidth / 2.)
        self.xProfileMax = int(xProfileMid + xProfileWidth / 2.)
        self.yProfileMin = int(yProfileMid - yProfileWidth / 2.)
        self.yProfileMax = int(yProfileMid + yProfileWidth / 2.)
        self.xProfileWidth = xProfileWidth
        self.yProfileWidth = yProfileWidth

    def getXProfile(self):
        """ Return the X profile data as a numpy array.
        FIXME - if the profile width is greater than 1 we will have a 
        two dimensional array"""
        xProfile = self.img[self.yProfileMin :
                            self.yProfileMax,
                            self.roi[X_ORIGIN] : 
                            self.roi[X_ORIGIN] + self.roi[X_SIZE]]
                            
        #print("xProfile=",xProfile, xProfile.shape)
        return(xProfile)

    def getYProfile(self):
        """ Return the Y profile data as a numpy array.
        FIXME - if the profile width is greater than 1 we will have a 
        two dimensional array"""
        yProfile = self.img[self.roi[Y_ORIGIN] : 
                            self.roi[Y_ORIGIN] + self.roi[Y_SIZE],
                            self.xProfileMin :
                            self.xProfileMax]
        yProfile = yProfile.transpose()
        #print("yProfile=",yProfile, yProfile.shape)
        return(yProfile)

    def getRoi(self):
        """ Return the ROI data as a numpy array """
        roi = self.img[self.roi[Y_ORIGIN] : 
                       self.roi[Y_ORIGIN] + self.roi[Y_SIZE],
                       self.roi[X_ORIGIN] : 
                       self.roi[X_ORIGIN] + self.roi[X_SIZE]]
        return roi

    def getStats(self,arr):
        """ Returns a tuple of statistics for array arr.
        elements are (min, mean, max, stdev, histogram bins, histogram values)
        """
        hist, bins = np.histogram(arr,256,(0,65536))
        #print(bins)
        return((arr.min(),arr.mean(), arr.max(), arr.std(), hist, bins))

    def getRoiStats(self):
        """ returns (mean, stdev) of the pixel intensities in the ROI
        """
        roi = self.getRoi()
        return(self.getStats(roi))

    def getXProfileStats(self):
        """ returns (mean, stdev) of the pixel intensities in the X Profile
        """
        profile = self.getXProfile()
        return(self.getStats(profile))

    def getYProfileStats(self):
        """ returns (mean, stdev) of the pixel intensities in the Y Profile
        """
        profile = self.getYProfile()
        return(self.getStats(profile))

    def getXProfileChart(self):
        """ returns an image of a graph of the X profile statistics """
        xProfile = self.getXProfile()
        xData = np.linspace(0,xProfile.shape[1]-1,xProfile.shape[1])
        fig, ax = plt.subplots( nrows=1, ncols=1 ) 
        ax.plot(xData,xProfile[0,:])
        ax.set_title("ROI X Intensity Profile")
        histImg = io.BytesIO()
        fig.savefig(histImg, format='png')
        histImg.seek(0)
        fig.savefig('roiXProfile.png')   # save the figure to file
        plt.close(fig)    # close the figure
        return(histImg)


    
    def getRoiImg(self):
        """ Returns a numpy array (cv2 image) of the image being analysed
        with the ROI highlighted as a square.
        """
        roiImg = cv2.cvtColor(self.img,cv2.COLOR_GRAY2RGB)
        cv2.rectangle(roiImg,
                      (self.roi[X_ORIGIN], self.roi[Y_ORIGIN]),
                      (self.roi[X_ORIGIN] + self.roi[X_SIZE],
                       self.roi[Y_ORIGIN] + self.roi[Y_SIZE]),
                      (65535,0,0),
                      3)
        return(roiImg)

    def convertTo8Bit(self,img):
        # Convert to 8 bit image for display - note this assumes
        # that we have a 16 bit image for starters.
        #print(img.dtype)
        if (img.dtype=="uint16"):
            res8 = (img/256).astype('uint8')
        else:
            res8 = img
        return(res8)

    def resizeImgForWeb(self,img):
        """ Returns a re-sized image for web viewing """
        xMax = int(self.WEB_X_MAX)
        yMax = int(img.shape[0] * xMax / img.shape[1])

        if (yMax > self.WEB_Y_MAX):
            yMax = int(self.WEB_Y_MAX)
            xMax = int(img.shape[1] * yMax / img.shape[0])
        res = cv2.resize(img, dsize=(xMax,yMax),
                         interpolation=cv2.INTER_CUBIC)
        res8 = self.convertTo8Bit(res)
        return(res8)
    
        
if __name__ == "__main__":
    print("imgAnalyser.__main__()")


    parser = argparse.ArgumentParser(description='CCD Camera Server')
    parser.add_argument('--sim', dest='simulator', action='store_true',
                        help='Use the simulator rather than the real camera')

    argsNamespace = parser.parse_args()
    args = vars(argsNamespace)
    print(args)

