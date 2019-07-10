#!/usr/bin/env python

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
    parser.add_argument('--debug', dest='debug', action="store_true",
                        help='Output Filename')

    argsNamespace = parser.parse_args()
    args = vars(argsNamespace)
    print(args)

    inDir = args['inDir']
    outFile = args['outFile']
    debug = args['debug']

    if (outFile is not None):
        of = open(outFile,"w")
    else:
        of = sys.stdout

    if (os.path.exists(inDir)):
        print("Processing images from folder %s" % inDir)
        dirlist = []
        for file in os.listdir(inDir):
            if file.endswith(IMG_EXTS):
                fpath = os.path.join(inDir, file)
                ctime = os.stat(fpath).st_ctime
                #print(fpath, ctime)
                dirlist.append((ctime,fpath))

        results = []
        dirlist = sorted(dirlist)

        for ctime,fpath in dirlist:
            #print(ctime,fpath)
            sys.stdout.write('.')
            sys.stdout.flush()
            ia = imgAnalyser.ImgAnalyser(fpath)
            ia.setRoi((380,350,200,1800))

            if (debug):
                print("roi origin=(%d,%d), size=(%d,%d)" %
                      (ia.roi[0],ia.roi[1],ia.roi[2],ia.roi[3]))
                print("xProfileMin=%d, xProfileMax=%d" %
                      (ia.xProfileMin, ia.xProfileMax))
                print("yProfileMin=%d, yProfileMax=%d" %
                      (ia.yProfileMin, ia.yProfileMax))
                roiImg = ia.resizeImgForWeb(ia.getRoiImg())
                cv2.imshow("roiImg",roiImg)
                cv2.waitKey(0)
                xProf = ia.getXProfile()
                print("xProf=",xProf)
                fig, ax = plt.subplots( nrows=1, ncols=1 ) 
                ax.plot(xProf[0,:])
                ax.set_title("ROI X Intensity Profile")
                plt.show()

            roiStats = ia.getRoiStats()
            #print(roiStats)
            xStats = ia.getXProfileStats()
            #print(xStats)
            yStats = ia.getYProfileStats()
            #print(yStats)

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
            

            
