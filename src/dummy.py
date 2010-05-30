#!/usr/bin/env python
#

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

import cdmi

class CDMIServer( HTTPServer ):
    debug = False
    allow_reuse_address = True

    def __init__(self, address, handler ):
        HTTPServer.__init__(self, address, handler )

class CDMIRequestHandler( BaseHTTPRequestHandler ):

    server_version = "CMDI-Dummy/dev"
    protocol_version = "HTTP/1.1"

    def do_REQUEST(self ):

        try:
            self.request = cdmi.Request( self.command, self.path, self.headers )
            if self.request.expects:
                self.request.read( self.rfile )
            self.request.phase2()
        except cdmi.ProtocolError, e:
            return self.send_error( 400, e )

        self.cdmi_handle()

    do_GET    = do_REQUEST
    do_POST   = do_REQUEST
    do_PUT    = do_REQUEST
    do_DELETE = do_REQUEST


    def cdmi_handle(self ):
        method = self.request.method
        path = self.request.path

        content = repr(self.request) + "\r\n"

        self.send_response( 200 )
        self.send_default_headers()
        self.send_header( "Content-Type", "text/plain" )
        self.send_header( "Content-Length", len(content) )
        self.end_headers()
        self.wfile.write( content )
        self.wfile.close()


    def send_default_headers(self ):
        self.send_header( "X-Author", "Koen Bollen" )

    def send_error(self, code, message=None ):
        if not message or not self.server.debug:
            message = self.responses[code][0]
        content = "error: %s (%d)\r\n" % (message,code)

        self.send_response( code, message )
        self.send_default_headers()
        self.close_connection = 1
        self.send_header( "Connection", "close" )
        self.send_header( "Content-Type", "text/plain" )
        self.send_header( "Content-Length", len(content) )
        self.end_headers()
        self.wfile.write( content )
        self.wfile.close()

def test(): # dev main only
    s = CDMIServer( ('',2364), CDMIRequestHandler )
    s.debug = True
    try:
        s.serve_forever()
    except KeyboardInterrupt:
        print "quit"

if __name__ == "__main__":
    test()

# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=79:

