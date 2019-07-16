#
# imgAnalyserTest.py
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
''' Unit Tests for the imgAnalyser module '''

import unittest
import numpy as np
import cv2
import matplotlib.pyplot as plt
import imgAnalyser
import sys

class TestImgAnalyser(unittest.TestCase):

    def setUp(self):
        self.ia = imgAnalyser.ImgAnalyser()
        self.testImg = np.array([[0,1,2],[3,4,5],[6,7,8],[9,10,11]])
        
    def test_setImg(self):
        self.ia.setImg(self.testImg)

        self.assertEqual(self.ia.imgSizeX,3,'incorrect imgSizeX')
        self.assertEqual(self.ia.imgSizeY,4,'incorrect imgSizeY')


    def test_setRoi(self):
        self.ia.setImg(self.testImg)

        # Test basic ROI setting
        self.ia.setRoi((1,1,2,2))
        self.assertEqual(self.ia.roi[0],1,'roi Xorigin incorrect')
        self.assertEqual(self.ia.roi[1],1,'roi Yorigin incorrect')
        self.assertEqual(self.ia.roi[2],2,'roi Xsize incorrect')
        self.assertEqual(self.ia.roi[3],2,'roi Ysize incorrect')

        # Test negative Yorigin
        self.ia.setRoi((-1,1,2,2))
        self.assertEqual(self.ia.roi[0],0,'roi Xorigin incorrect')
        self.assertEqual(self.ia.roi[1],1,'roi Yorigin incorrect')
        self.assertEqual(self.ia.roi[2],2,'roi Xsize incorrect')
        self.assertEqual(self.ia.roi[3],2,'roi Ysize incorrect')

        # Test negative Yorigin
        self.ia.setRoi((0,-1,2,2))
        self.assertEqual(self.ia.roi[0],0,'roi Xorigin incorrect')
        self.assertEqual(self.ia.roi[1],0,'roi Yorigin incorrect')
        self.assertEqual(self.ia.roi[2],2,'roi Xsize incorrect')
        self.assertEqual(self.ia.roi[3],2,'roi Ysize incorrect')

        # Test XSize overflow
        self.ia.setRoi((1,1,4,2))
        self.assertEqual(self.ia.roi[0],1,'roi Xorigin incorrect')
        self.assertEqual(self.ia.roi[1],1,'roi Yorigin incorrect')
        self.assertEqual(self.ia.roi[2],2,'roi Xsize incorrect')
        self.assertEqual(self.ia.roi[3],2,'roi Ysize incorrect')

        # Test YSize overflow
        self.ia.setRoi((1,1,4,4))
        self.assertEqual(self.ia.roi[0],1,'roi Xorigin incorrect')
        self.assertEqual(self.ia.roi[1],1,'roi Yorigin incorrect')
        self.assertEqual(self.ia.roi[2],2,'roi Xsize incorrect')
        self.assertEqual(self.ia.roi[3],3,'roi Ysize incorrect')

        # Test Non-integer ROI
        self.ia.setRoi((1.5,1,4,4))
        self.assertEqual(self.ia.roi[0],1,'roi Xorigin incorrect')
        self.assertEqual(self.ia.roi[1],1,'roi Yorigin incorrect')
        self.assertEqual(self.ia.roi[2],2,'roi Xsize incorrect')
        self.assertEqual(self.ia.roi[3],3,'roi Ysize incorrect')
        

    def test_setSetProfiles(self):
        self.ia.setImg(self.testImg)

        self.ia.setRoi((0,0,2,2))
        self.ia.setProfiles()
        self.assertEqual(self.ia.xProfileWidth,1,'xProfileWidth incorrect')
        self.assertEqual(self.ia.yProfileWidth,1,'yProfileWidth incorrect')

        self.ia.setProfiles(3,1)
        self.assertEqual(self.ia.xProfileWidth,2,'xProfileWidth incorrect')
        self.assertEqual(self.ia.yProfileWidth,1,'yProfileWidth incorrect')
        self.ia.setProfiles(1,3)
        self.assertEqual(self.ia.xProfileWidth,1,'xProfileWidth incorrect')
        self.assertEqual(self.ia.yProfileWidth,2,'yProfileWidth incorrect')


    def test_getXProfileData(self):
        self.ia.setImg(self.testImg)
        self.ia.setRoi((0,0,3,3),(2,2))
        xProfile = self.ia.getXProfile()
        #print(xProfile)
        correctxProfile = np.array([[1.5,2.5,3.5]])
        #print(correctxProfile)

        self.ia.setRoi((0,0,3,4),(2,2))
        yProfile = self.ia.getYProfile()
        print("yProfile=",yProfile)
        correctProfile = np.array([0.5,3.5,6.5,9.5])
        print("correctProfile=",correctProfile)
        sys.stdout.flush()
        self.assertEqual(np.allclose(xProfile,correctxProfile),True,"Xprofile wrong")
        self.assertEqual(np.allclose(yProfile,correctProfile),True,"Yprofile wrong")

    def test_getRoi(self):
        self.ia.setImg(self.testImg)
        self.ia.setRoi((0,0,2,2))
        roi = self.ia.getRoi()
        #print(roi)
        correctProfile = np.array([[0,1],[3,4]])
        #print(correctProfile)
        self.assertEqual(np.allclose(roi,correctProfile),True,"roi wrong")


    def test_realImage(self):
        self.ia.setImg("./test_image.tif")
        self.ia.setRoi((380,350,200,1800))

        roiImg = self.ia.resizeImgForWeb(self.ia.getRoiImg())
        cv2.imshow("roiImg",roiImg)
        cv2.waitKey(0)

        roiStats = self.ia.getRoiStats()
        #print(roiStats)
        xStats = self.ia.getXProfileStats()
        #print(xStats)
        yStats = self.ia.getYProfileStats()
        #print(yStats)

        self.assertAlmostEqual(roiStats[3]/roiStats[1],0.167,3,"ROI SD%")

if __name__ == '__main__':
    unittest.main()
