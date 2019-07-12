#!/usr/env python
#
# WebControlClass
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
#
''' WebControlClass An Abstract(ish) class that provides a simple web interface.
The idea is that it is sub-classed and the sub-classes override the
on wwwRequest() function to actually respond to requests received over
the web.
'''
import time
import bottle
import os
import urllib.request
import threading

print(os.path.dirname(os.path.realpath(__file__)))



class WebControlClass:
    shutDown = False
    scriptDir = None
    def __init__(self,portNo = 8080):
        ''' Initialise this WebControlClass to serve data on port Number
        portNo (default = 8080.
        '''
        print("WebControlClass.__init__(portNo=%d)" % (int(portNo)))
        self.portNo = portNo
        self.scriptDir = os.path.dirname(os.path.realpath(__file__))
        self.wwwPath = os.path.join(self.scriptDir,'www')
        print("wwwPath=%s" % self.wwwPath)

    def getWwwPath(self):
        return(self.wwwPath)

    def startServer(self):
        wwwThread = threading.Thread(target=self._startServer)
        wwwThread.start()
        print("wwwThread started")
        
    def _startServer(self):
        ''' Start the web server'''
        app = bottle.Bottle()
        self.app = app

        @app.route('/static/<filepath:path>')
        def server_static(filepath):
            return bottle.static_file(filepath, root=self.wwwPath)

        @app.route('/')
        @app.route('/index.html')
        def index():
            return(server_static('index.html'))

        @app.route('/favicon.ico')
        def favicon():
            return(server_static('favicon.ico'))

        @app.route('/<cmdStr>/<valStr>', method=['PUT','POST','GET','DELETE'])
        @app.route('/<cmdStr>/', method=['PUT','POST','GET','DELETE'])
        @app.route('/<cmdStr>', method=['PUT','POST','GET','DELETE'])
        def cmd(cmdStr,valStr='None'):
            #print("WebControlClass.cmd(%s, %s)" % (cmdStr,valStr))
            return self.onWwwCmd(cmdStr, valStr,bottle.request.method, bottle.request)

        bottle.run(app,host='0.0.0.0', port=self.portNo)

    def onWwwCmd(self,cmdStr,valStr, methodStr,request):
        ''' Process the command, with parameter 'valStr' using request
        method methodStr, and return the appropriate response.
        request is the bottlepy request associated with the command
        '''
        print("WebControlClass.onWwwCmd(%s/%s %s)" % (cmdStr,valStr,methodStr))
        print("Override this method to make it do something useful!!!!")
        return('<h1>FIXME</h1>'
               'Override onWwwCmd() to make it do something useful!!!!'
               '<br/>cmdStr=%s/%s, method=%s' % (cmdStr,valStr,methodStr))


    def getDataFromServer(self,urlStr):
        ''' Download data from a server using the specified URL.
        '''
        response = urllib.request.urlopen(urlStr)
        data = response.read()
        return data

if __name__ == "__main__":
    wcc = WebControlClass()
    #print(wcc.getDataFromServer("http://google.co.uk"))
    wcc.startServer()
    print("wcc.startServer() completed")
