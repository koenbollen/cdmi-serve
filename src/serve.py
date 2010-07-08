# Koen Bollen <meneer koenbollen nl>
# 2010 GPL

from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import logging

try:
    import json
except ImportError:
    import simplejson as json

import cdmi

class CDMIServer( ThreadingMixIn, HTTPServer ):
    debug = False
    allow_reuse_address = True

    def __init__(self, address, handler, io ):
        HTTPServer.__init__(self, address, handler )
        self.io = io

    def close(self ):
        logging.info( "quit" )

class CDMIRequestHandler( BaseHTTPRequestHandler ):

    server_version = "CMDI-Serve/dev"
    protocol_version = "HTTP/1.1"

    def do_REQUEST(self ):

        if self.server.debug:
            if self.path.startswith( "/cdmi_generate_" ):
                try:
                    code = int( self.path[15:] )
                except ValueError:
                    code = 400
                return self.send_error( code )

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
        debug = self.server.debug
        io = self.server.io
        iscdmi = self.request.cdmi
        method = self.request.method
        path = self.request.path
        headers = self.request.headers
        objecttype = self.request.objecttype

        # The only possibility that the objecttype is
        # unknown is on a non-cdmi request for reading
        # or deleting a dataobject or container:
        if not iscdmi and method in ("get", "delete"):
            if objecttype == "unknown":
                if not io.exists( path ):
                    return self.send_error( 404 )
                if objecttype == "unknown":
                    self.request.objecttype = objecttype = io.objecttype( path)
        if iscdmi and objecttype == "unknown":
            if not io.exists( path ):
                return self.send_error( 404 )
            self.request.objecttype = objecttype = io.objecttype( path)

        assert objecttype != "unknown"

        # Loose checks:
        if not iscdmi and method=="get":
            if objecttype=="container" and len(self.request.fields) == 0:
                return self.send_error( 400, "missing fields" )

        # Call the object type specific parse method:
        try:
            typemthd = getattr( self.request, objecttype )
        except AttributeError:
            pass
        else:
            try:
                typemthd()
            except cdmi.ProtocolError, e:
                return self.send_error( 400, e )

        if debug:
            if "x-debug-sleep" in headers:
                try:
                    from time import sleep
                    sleep( int( headers['x-debug-sleep'] ) )
                except ValueError:
                    pass

        handler = cdmi.Handler( self.request, io )
        try:
            mname = method+"_"+objecttype
            logging.debug( "deploying request to cdmi.Handler.%s", mname )
            mthd = getattr( handler, mname )
        except AttributeError, e:
            return self.send_error(
                    501,
                    "method 'cdmi.Handler.%s' not implemented" % mname
                )
        try:
            res = mthd()
        except cdmi.OperationError, e:
            return self.send_error( e.httpcode, "%s: %s"%(e.message, e.cause))

        if res is not False:
            if res[1] is None:
                self.send_response( *res[0] )
                self.send_default_headers()
                self.send_header( "Content-Length", 0 )
                self.end_headers()
            elif isinstance(res[1], file):
                response, fp, length, offset, contenttype = res
                self.send_response( *response )
                self.send_default_headers()
                self.send_header( "Content-Type", contenttype )
                self.send_header( "Content-Length", length )
                if self.request.range is not None and length > 0:
                    rangestr = "bytes=%d-%d" % ( offset, offset+length-1 )
                    self.send_header( "Content-Range", rangestr )
                self.end_headers()
                nbytes = 0
                while nbytes < length:
                    l = min( length-nbytes, self.server.io.bufsize )
                    chunk = fp.read( l )
                    if not chunk:
                        break
                    self.wfile.write( chunk )
                    nbytes += len( chunk )
                fp.close()
            else:
                data = json.dumps( res[1], indent=debug and 2 or None ).strip() + "\r\n"
                self.send_response( *res[0] )
                self.send_default_headers()
                if iscdmi:
                    mimetype = cdmi.mimetypes[objecttype]
                    self.send_header( "Content-Type", mimetype )
                else:
                    self.send_header( "Content-Type", "text/json" )
                self.send_header( "Content-Length", len(data) )
                self.end_headers()
                self.wfile.write( data )


    def send_default_headers(self ):
        self.send_header( "X-Author", "Koen Bollen" )


    def send_error(self, code, message=None ):
        if not message or not self.server.debug:
            message = self.responses[code][0]
        content = "error: %s (%d)\r\n" % (message,code)

        self.send_response( code, message )
        self.send_default_headers()
        if code >= 500 and code != 501:
            self.send_header( "Connection", "close" )
            self.close_connection = 1
        self.send_header( "Content-Type", "text/plain" )
        self.send_header( "Content-Length", len(content) )
        self.end_headers()
        self.wfile.write( content )

    def log_message(self, format, *args):
        msg = "%s %s" % ( self.address_string(), format%args )
        logging.info( msg )

# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=79:

