#!/usr/bin/env python
#
# imgSequenceAnalyser.py
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

'''imgSequenceAnalyser - A command line tool to take a directory full
of images and apply the same analysis to each, to produce a sequence of
analysis results.
'''
import os
import io
import sys
import numpy as np
import cv2
import matplotlib.pyplot as plt
import argparse
import imgAnalyser

IMG_EXTS = (".tif", ".TIF", ".png", ".PNG", ".fit",  ".FIT", ".fits", ".FITS")
        
if __name__ == "__main__":
    print("imgSequenceAnalyser.__main__()")

    parser = argparse.ArgumentParser(description='Image Sequence Analyser')
    parser.add_argument('--inDir', dest='inDir', required=True,
                        help='Directory containing the images to be processed')
    parser.add_argument('--outFile', dest='outFile',
                        help='Output Filename')
    parser.add_argument('--roi', dest='roiStr',
                        help='Region of Interest <xorigin>,<yorigin>:<xsize>,<ysize>')
    parser.add_argument('--debug', dest='debug', action="store_true",
                        help='Output Filename')

    argsNamespace = parser.parse_args()
    args = vars(argsNamespace)
    print(args)

    inDir = args['inDir']
    outFile = args['outFile']
    debug = args['debug']
    roiStr = args['roiStr']

    if (outFile is not None):
        of = open(outFile,"w")
    else:
        of = sys.stdout

    if (os.path.exists(inDir)):
        dirlist = []
        if (os.path.isdir(inDir)):
            print("Processing images from folder %s" % inDir)
            for file in os.listdir(inDir):
                if file.endswith(IMG_EXTS):
                    fpath = os.path.join(inDir, file)
                    ctime = os.stat(fpath).st_ctime
                    #print(fpath, ctime)
                    dirlist.append((ctime,fpath))
        else:
            ctime = os.stat(inDir).st_ctime
            dirlist.append((ctime,inDir))
            
        results = []
        dirlist = sorted(dirlist)
        firstRow = True

        for ctime,fpath in dirlist:
            sys.stdout.write('%s\n' % fpath)
            sys.stdout.flush()
            ia = imgAnalyser.ImgAnalyser(fpath)
            if (roiStr == None):
                imSize = ia.getImgSize()
                roi = (0, 0, imSize[0], imSize[1])
            else:
                roi = ia.str2roi(roiStr)
            # ia.setRoi((380,350,200,1800))  # Sharp Edge
            #ia.setRoi((195,114,20,1780)) # Slit
            #print(roiStr,roi)
            ia.setRoi(roi)

            roiStats = ia.getRoiStats()
            #print(roiStats)
            xStats = ia.getXProfileStats()
            #print(xStats)
            yStats = ia.getYProfileStats()
            #print(yStats)
            
            roiImg = ia.resizeImgForWeb(ia.getRoiImg())

            xProf = ia.getXProfile()
            yProf = ia.getYProfile()
            #print("xProf=",xProf)
            #print("yProf=",yProf)
            fig = plt.figure(constrained_layout=True)
            ax1 = plt.subplot2grid((2,2),(0,0), colspan=1)
            ax2 = plt.subplot2grid((2,2),(1,0), colspan=1)
            ax3 = plt.subplot2grid((2,2),(0,1), rowspan=2)

            ax1.plot(xProf[0,:])
            ax1.set_title("ROI X Intensity Profile (%3.1f%%)" %
                          (100. * xStats[3] / xStats[1]),
                          fontsize="x-small")
            ax2.plot(yProf[0,:])
            ax2.set_title("ROI Y Intensity Profile (%3.1f%%)" %
                          (100. * yStats[3] / yStats[1]), fontsize="x-small")
            ax3.imshow(roiImg)
            fig.suptitle(fpath, fontsize="x-small")
            #fig.set_tight_layout(True)
            fig.set_constrained_layout(True)

            figFname = "%s_analysis.png" % fpath
            plt.savefig(figFname)

            if (debug):
                print("roi origin=(%d,%d), size=(%d,%d)" %
                      (ia.roi[0],ia.roi[1],ia.roi[2],ia.roi[3]))
                print("xProfileMin=%d, xProfileMax=%d" %
                      (ia.xProfileMin, ia.xProfileMax))
                print("yProfileMin=%d, yProfileMax=%d" %
                      (ia.yProfileMin, ia.yProfileMax))
                plt.show()

            plt.close()
            
            if (firstRow):
                firstRow = False
                outRow = []
                outRow.append("Timestamp")
                outRow.append("File")
                outRow.append("ROI_min")  # roi Min
                outRow.append("ROI_mean")  # roi Mean
                outRow.append("ROI_max")  # roi Max
                outRow.append("ROI_stdDev (%)") # stDev (%)
                outRow.append("X_min") # x-min
                outRow.append("X_mean") # x-mean
                outRow.append("X_max") # x-max
                outRow.append("X_stdDev (%)") # x-stdev (%)
                outRow.append("Y_min") # x-min
                outRow.append("Y_mean") # x-mean
                outRow.append("Y_max") # x-max
                outRow.append("Y_stdDev (%)") # x-stdev (%)
                results.append(outRow)
                
            outRow = []
            outRow.append(ctime)
            outRow.append(fpath)
            outRow.append(roiStats[0])  # roi Min
            outRow.append(roiStats[1])  # roi Mean
            outRow.append(roiStats[2])  # roi Max
            outRow.append(100. * roiStats[3] / roiStats[1]) # stDev (%)
            outRow.append(xStats[0]) # x-min
            outRow.append(xStats[1]) # x-mean
            outRow.append(xStats[2]) # x-max
            outRow.append(100. *xStats[3] / xStats[1]) # x-stdev (%)
            outRow.append(yStats[0]) # y-min
            outRow.append(yStats[1]) # y-mean
            outRow.append(yStats[2]) # y-max
            outRow.append(100. *yStats[3] / yStats[1]) # y-stdev (%)
            
            results.append(outRow)

        for row in results:
            for item in row:
                of.write(str(item))
                of.write(", ")
            of.write("\n")

        if (outFile is not None):
            of.close()
            

            
