import unittest
import numpy as np
import cv2
import matplotlib.pyplot as plt
import imgAnalyser

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
        self.ia.setRoi((0,0,3,3))
        xProfile = self.ia.getXProfile()
        #print(xProfile)
        correctProfile = np.array([[3,4,5]])
        #print(correctProfile)
        self.assertEqual(np.allclose(xProfile,correctProfile),True,"Xprofile wrong")

        self.ia.setRoi((0,0,3,4))
        yProfile = self.ia.getYProfile()
        #print(yProfile)
        correctProfile = np.array([[1],[4],[7],[10]])
        #print(correctProfile)
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
        img = cv2.imread("./test_image.tif",cv2.IMREAD_GRAYSCALE)
        self.ia.setImg(img)
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

        self.assertAlmostEqual(roiStats[3]/roiStats[1],0.169,3,"ROI SD%")

        xProfImg = self.ia.getXProfileChart()
        cv2.imshow("xprof",xProfImg)
        cv2.waitKey(0)
        
if __name__ == '__main__':
    unittest.main()
