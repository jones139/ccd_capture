ccd_capture README
==================

ccd_capture.py is a small web server that provides a web based interface
to capture CCD camera images.

It relies on an INDI server running on the same computer to provide the
interface to the camera hardware.

The web interface appears as http://localhost:8081

Installation - Works on Ubuntu 18.04
====================================
Install the INDI server
	sudo add-apt-repository ppa:mutlaqja/ppa
	sudo apt-get update
	sudo apt install indi-atik indi-full indi-bin libindi-dev

Set up Python environment
        sudo apt install build-essential python3-pip libz3-dev python-setuptools python-dev libindi-dev swig python3-gi-cairo python3-gi gir1.2-gtk-3.0 pkg-config libcairo-dev libgirepository1.0-dev
    	sudo apt install python-setuptools python-dev libindi-dev swig
	sudo apt install libcfitsio-dev libnova-dev virtualenv

Create and activate a python3 virtual environment
	sudo pip3 install virtualenvwrapper
	Add the following to ~/.bashrc:
		export WORKON_HOME=$HOME/.virtualenvs
		export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
		#export PROJECT_HOME=$HOME/Devel
		source /usr/local/bin/virtualenvwrapper.sh
	source ~/.bashrc
	mkvirtualenv --python=/usr/bin/python3 py3
	workon py3
Install Python packages
	pip install pyindi-client
	pip install numpy astropy gobject PyGObject opencv-python pypng scipy
	pip install matplotlib pdoc3


User Instructions
============
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


Software Description
====================
The interface to the camera is included in the ccd_capture.py file and uses the
pyIndi library to connect to the INDI server.   We use the astropy.io.fits
library to interpret the fits data provided by the camera interface.

WebControlClass.py provides a (sort of) abstract class for a web control
application using the bottle.py framework, and is used as the basis of
ccd_capture.py

The image analysis and plotting uses opencv and matplotlib.

ccd_capture.py provides a simple REST(ish) interface to the camera.
The web browser runs www/index.html, which executes javascript code in
www/js/ccd_capture.js.

The web interface is quite old fashioned - it uses jquery rather than a modern
javascript framework to make it easier for someone else to work out how it works.
The style of the web page uses the bootstrap V4 style library.

The javascript performs a getData request on the ccd_capture server every second
and updates the web page based on the data.
The onClick events of the various buttons trigger functions that make other API
calls to ccd_capture to set parameters etc.

Generate the code documentation using
	 pdoc3 --html -o docs ccd_capture imgAnalyser WebControlClass imgSequenceAnalyser


Graham Jones
10 July 2019
     
