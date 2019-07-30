#!/usr/bin/env/python

import numpy as np
import sep
import cv2
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.patches import Ellipse
from sklearn.linear_model import LinearRegression


rcParams['figure.figsize'] = [10., 8.]

data = cv2.imread("PS_1.tif",cv2.IMREAD_ANYDEPTH)
print("Read Image - depth=",data.dtype)
data = data.astype('float32')
print("Read Image - depth=",data.dtype)


# show the image
m, s = np.mean(data), np.std(data)


# measure a spatially varying background on the image
bkg = sep.Background(data)

# get a "global" mean and noise of the image background:
print("background:",bkg.globalback)
print("background rms:",bkg.globalrms)

# evaluate background as 2-d array, same size as original image
bkg_image = bkg.back()

data_sub = data - bkg

objects = sep.extract(data=data_sub, thresh=3, err=bkg.globalrms)
print("found %d objects" % len(objects))

ps = []
vertPosn = []
horizPosn = []
for ob in objects:
    print("(%d,%d) - peak=%.0f,%.0f" % (ob['x'],ob['y'],ob['peak'],ob['cpeak']))
    ps.append((ob['x'],ob['y'],ob['cpeak'],ob['flux']))


ps.sort(key=lambda tup: tup[2], reverse = True)
ps = ps[:8]  # Select only brightest 8 objects
# Then sort back into y order
ps.sort(key=lambda tup: tup[1], reverse = False)

print("")
print("Selected point sources")
for p in ps:
    print("(%d,%d) - peak=%.0f, flux=%.0f" % (p[0],p[1],p[2],p[3]))
    vertPosn.append(p[1])
    horizPosn.append(p[0])
    


vertPosn = np.asarray(vertPosn).reshape((-1,1))
horizPosn = np.asarray(horizPosn)

print("vertPosn",vertPosn)
print("horizPosn",horizPosn)
#model = LinearRegression
#model.fit(vertPosn, horizPosn)
#print("Straight Line Fit to Pont Centres: intercept=%f, gradient=%f" %
#      (model.intercept_,model.coef_[0]))

res = np.linalg.lstsq(vertPosn, horizPosn, rcond = None)[0:2]
print(res)

m = res[0][0]
c = res[1][0]

print(m,c)



    
# plot background-subtracted image
fig, ax = plt.subplots(2,2)
print(ax)
m, s = np.mean(data), np.std(data)
ax[0][0].imshow(data, interpolation='nearest', cmap='gray',
               vmin=m-s, vmax=m+s, origin='lower')
m, s = np.mean(bkg_image), np.std(bkg_image)
ax[0][1].imshow(bkg_image, interpolation='nearest', cmap='gray',
               vmin=m-s, vmax=m+s, origin='lower')

ax[1][1].plot(vertPosn,horizPosn)

m, s = np.mean(data_sub), np.std(data_sub)
im = ax[1][0].imshow(data_sub, interpolation='nearest', cmap='gray',
               vmin=m-s, vmax=m+s, origin='lower')

# plot an ellipse for each object
for i in range(len(objects)):
    e = Ellipse(xy=(objects['x'][i], objects['y'][i]),
                width=6*objects['a'][i],
                height=6*objects['b'][i],
                angle=objects['theta'][i] * 180. / np.pi)
    e.set_facecolor('none')
    e.set_edgecolor('yellow')
    ax[1][0].add_artist(e)
    
plt.show()
