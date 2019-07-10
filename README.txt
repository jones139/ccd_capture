ccd_capture README
==================

ccd_capture.py is a small web server that provides a web based interface
to capture CCD camera images.

It relies on an INDI server running on the same computer to provide the
interface to the camera hardware.

The web interface appears as http://localhost:8081


To start the INDI server run:
   indiserver -vv indi_atik_ccd

For testing you can use the INDI simulator instead by using:
    indiserver -vv indi_simulator_ccd indi_simulator_telescope
(Note that you need the telescope simulator for the ccd simulator to function)

Then start the ccd_capture.py web server by activating a python3 environment
such as
     workon py3

Then running
     python ./ccd_capture.py     (to use the Atik camera) or
     python ./ccd_capture.py --sim (to use the simulator)

Then point a web browser at http://localhost:8081, or you can replace localhost with the ip address of the computer to access it from another computer.

The web interface provides the following functions:
   - Set the exposure time
   - Set the camera cooler setpoint (not working yet!)
   - Set the subframe to determine which part of the camera ccd data is downloaded (use a smaller subframe to get a faster frame rate).
   - Set the region of interest that is subjected to quantitative analysis for each image.
   - Collect a single image
   - Collect images continuously
   - Save images to disk on demand, or automatically save each image.

The saved images appear in ./ccd_capture/www/data.
Note that at the moment we do not provide a function to download the images
via the web interface.


Graham Jones
10 July 2019
     
