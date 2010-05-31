#!/usr/bin/env python
#

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

import cdmi
import io as _io

class CDMIServer( HTTPServer ):
    debug = False
    allow_reuse_address = True

    def __init__(self, address, handler, io ):
        HTTPServer.__init__(self, address, handler )
        self.io = io

class CDMIRequestHandler( BaseHTTPRequestHandler ):

    server_version = "CMDI-Dummy/dev"
    protocol_version = "HTTP/1.1"

    def do_REQUEST(self ):

        try:
            self.request = cdmi.Request( self.command, self.path, self.headers )
            self.request.read( self.rfile )
        except cdmi.ProtocolError, e:
            return self.send_error( 400, e )

        self.cdmi_handle()

    do_GET    = do_REQUEST
    do_POST   = do_REQUEST
    do_PUT    = do_REQUEST
    do_DELETE = do_REQUEST


    def cdmi_handle(self ):

        # This suppose to speed things up:
        io = self.server.io
        iscdmi = self.request.cdmi
        method = self.request.method
        path = self.request.path

        # The only possibility that the objecttype is
        # unknown is on a non-cdmi request for reading
        # or deleting a dataobject or container:
        if not iscdmi and method in ("get", "delete"):
            if not io.exists( path ):
                return self.send_error( 404 )
            if self.request.objecttype == "unknown":
                self.request.objecttype = io.objecttype( path)

        assert self.request.objecttype != "unknown"

        mname = method+"_"+self.request.objecttype

        # tmp test, i'll read rawdata as next request otherwise:
        rawdata = None
        if self.request.source and self.request.source[0] == "rawdata":
            try:
                length = self.request.headers['Content-Length']
                length = int(length)
            except KeyError:
                length = None
            rawdata = self.rfile.read(length)
            self.request.source = ("rawdata", rawdata)

        content  = repr(self.request) + "\r\n"
        content += "methodname: "+mname+"\r\n"
        content += "source: "+repr(self.request.source)+"\r\n"

        self.send_response( 200 )
        self.send_default_headers()
        self.send_header( "Content-Type", "text/plain" )
        self.send_header( "Content-Length", len(content) )
        self.end_headers()
        self.wfile.write( content )


    def send_default_headers(self ):
        self.send_header( "X-Author", "Koen Bollen" )


    def send_error(self, code, message=None ):
        if not message or not self.server.debug:
            message = self.responses[code][0]
        content = "error: %s (%d)\r\n" % (message,code)

        self.send_response( code, message )
        self.send_default_headers()
        if code >= 500:
            self.send_header( "Connection", "close" )
            self.close_connection = 1
        self.send_header( "Content-Type", "text/plain" )
        self.send_header( "Content-Length", len(content) )
        self.end_headers()
        self.wfile.write( content )


def test(): # dev main only
    s = CDMIServer(
            ('',2364), CDMIRequestHandler,
            _io.IO( "data/" )
        )
    s.debug = True
    try:
        s.serve_forever()
    except KeyboardInterrupt:
        print "quit"

if __name__ == "__main__":
    test()

# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=79:

