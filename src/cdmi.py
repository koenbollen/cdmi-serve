# Koen Bollen <meneer@koenbollen.nl>
# 2010 GPL

SPECIFICATION_VERSION = 1.0
DEFAULT_PORT = 2364

from StringIO import StringIO
try:
    import json
except ImportError:
    import simplejson as json

import util

httpstatuscodes = [
    ( 200, "OK",
    "Resource retrieved successfully" ),
    ( 201, "Created",
    "Resource created successfully" ),
    ( 202, "Accepted",
    "Long running operation accepted for processing" ),
    ( 204, "No Content",
    "Operation successful, no data" ),
    ( 400, "Bad Request",
    "Missing or invalid request contents" ),
    ( 401, "Unauthorized",
    "Invalid authentication/authorization credentials" ),
    ( 403, "Forbidden",
    "This user is not allowed to perform this request" ),
    ( 404, "Not Found",
    "Requested resource not found" ),
    ( 405, "Method Not Allowed",
    "Requested HTTP verb not allowed on this resource" ),
    ( 406, "Not Acceptable",
    "No content type can be produced at this URI that matches the request" ),
    ( 409, "Conflict",
    "The operation conflicts with a non-CDMI access protocol lock, "
    + "or could cause a state transition error on the server." ),
    ( 500, "Internal Server Error",
    "An unexpected vendor specific error" ),
    ( 501, "Not Implemented",
    "A CDMI operation or metadata value was attempted that is not implemented.")
]

mimetypes = {
    'object':       "application/vnd.org.snia.cdmi.object+json",
    'container':    "application/vnd.org.snia.cdmi.container+json",
    'dataobject':   "application/vnd.org.snia.cdmi.dataobject+json",
    'domain':       "application/vnd.org.snia.cdmi.domain+json",
    'queue':        "application/vnd.org.snia.cdmi.queue+json",
    'capabilities': "application/vnd.org.snia.cdmi.capabilities+json",
}

class CDMIError( Exception ):
    pass

class ProtocolError( CDMIError ):
    def __init__(self, message, cause=None ):
        self.message = message
        self.cause = cause

    def __str__(self ):
        if self.cause:
            return "%s: %r" % (self.message, self.cause)
        return self.message

    def __repr__(self ):
        return "<CDMI.ProtocolError %s>" % (str(self))

class OperationError( CDMIError ):

    def __init__(self, httpcode, message, cause=None ):
        self.httpcode = httpcode
        self.message = message
        self.cause = cause

    def __str__(self ):
        if self.cause:
            return "%s (%d): %r" % (self.message, self.httpcode, self.cause )
        return "%s (%d)" % (self.message, self.httpcode )

    def __repr__(self ):
        return "<CDMI.OperationError %s>" % (str(self))

class Request( object ):

    def __init__(self, method, path, headers ):

        self.method = method.lower()
        self.path = path.strip()
        self.headers = headers
        self.cdmi = None
        self.objecttype = "unknown"
        self.source = None
        self.rawdata = None
        self.json = None
        self.range = None

        # states:
        self.__validated = False
        self.__parsed = False
        self.__read = False

        self.__validate()
        self.__parse()


    def __validate(self ):
        if self.method not in ("get", "post", "put", "delete"):
            raise ProtocolError( "invalid method:", self.method )
        if self.path[0] != '/':
            raise ProtocolError( "invalid path", self.path )
        self.__validated = True


    def __parse(self ):
        h = self.headers
        spec = h.get('X-CDMI-Specification-Version')
        self.cdmi = spec is not None
        if self.cdmi:

            try:
                if float(spec) < SPECIFICATION_VERSION:
                    raise ValueError
            except ValueError:
                raise ProtocolError( "incorrect cdmi version", spec )

            try:
                accept = h['Accept']
                contenttype = h['Content-Type']
            except KeyError, e:
                # One exception, a GET request without a type:
                if not (e.args[0].lower() == "accept" and self.method=="get"):
                    raise ProtocolError( "missing header", str(e) )
                accept = None

            for objecttype, mime in mimetypes.items():
                if accept == contenttype == mime:
                    self.objecttype = objecttype
                    break
                if self.method == "get" and accept == mime:
                    self.objecttype = objecttype
                    break
            if self.objecttype == "object":
                self.objecttype = "unknown"

            self.accept = accept
            self.contenttype = contenttype

        else:
            self.accept = None
            self.contenttype = h.get('Content-Type')
            if self.method in ("put","post"):
                if self.contenttype:
                    self.objecttype = "dataobject"
                else:
                    self.objecttype = "container"
            else:
                self.objecttype = "unknown"

        # Separate fields from the path:
        p = self.path
        self.fields = {}
        if "?" in self.path:
            self.path, fstr = self.path.split( "?", 1 )
            fields = [(f.split(":", 1)+[None])[:2] for f in fstr.split(";")]
            for k,v in fields:
                if v:
                    v = v.strip()
                self.fields[k.strip().lower()] = v

        self.__parsed = True

    def __repr__(self ):
        tmpl = "<cdmi request: {cdmi} {method} a {objecttype}: '{path}'>"
        values = vars(self)
        values['cdmi'] = self.cdmi and "cdmi" or "non-cdmi"
        return tmpl.format( **values )

    def read(self, fp ):
        """Read and parse request payload."""
        if self.__read:
            return

        self.fp = fp

        # Read json payload if needed:
        if self.cdmi and self.method not in ("get","delete"):

            try:
                length = self.headers['Content-Length']
                length = int(length)
            except KeyError:
                length = None
            except ValueError:
                raise ProtocolError( "invalid Content-Length", length )
            self.rawdata = fp.read(length)

            if self.contenttype=="text/json" or self.contenttype.endswith("+json"):
                try:
                    self.json = json.loads( self.rawdata )
                except ValueError, e:
                    raise ProtocolError( "unable to parse json", e.args[0] )


        if not self.cdmi and self.contenttype:
            try:
                length = self.headers['Content-Length']
                length = int(length)
            except KeyError:
                raise ProtocolError( "missing Content-Length" )
            except ValueError:
                raise ProtocolError( "invalid Content-Length", length )
            self.source = ( "rawdata", length )
        elif self.cdmi and self.method in ("post", "put"):
            if self.json is None:
                raise ProtocolError( "missing json payload" )
            for k in ("value", "copy", "move", "reference"):
                if k in self.json:
                    self.source = ( k, self.json[k] )
                    break

        self.__read = True

    def dataobject(self ):
        rangestr = None

        if self.cdmi:
            if "value" in self.fields and self.fields['value'] is not None:
                rangestr = "bytes=" + self.fields['value']
        else:
            if "Content-Range" in self.headers:
                rangestr = self.headers['Content-Range']

        if rangestr is not None:
            self.range = util.byterange( rangestr )
        else:
            self.range = None

    def container(self ):
        if "children" in self.fields and self.fields['children'] is not None:
            try:
                range = [int(p) for p in self.fields['children'].split("-")]
            except ValueError:
                raise ProtocolError( "invalid children range", self.fields['children'] )
            range = (range + [None]*2)[:2]
            if range[1] is not None:
                range[1] += 1
            self.range = tuple(range)


class Handler( object ):

    def __init__(self, request, io ):
        self.request = request
        self.io = io
        self.target = io.buildtarget( self.request.path )

    def put_container(self ):
        target = self.target

        noclobber = self.request.headers.get("X-CDMI-NoClobber", "false") # TEST
        noclobber = noclobber.strip().lower() in ("true","yes","1")

        if target.exists():
            if target.objecttype() != "container" or noclobber:
                raise OperationError( 409, "path exists" )

        stype = self.request.source[0]
        if stype in ("move","copy","reference"):
            raise OperationError( 501, "not yet implemented", stype )

        try:
            target.mkdir()
        except OSError, e:
            httpcode = 500
            if e.errno == 2:
                httpcode = 404
            if e.errno != 17 and not noclobber: # File exists
                raise OperationError( httpcode, "unable to create directory", e );

        # save user metadata here

        reply = None
        if self.request.cdmi:
            try:
                children = target.list()
            except OSError: # doesnt happen
                children = []
            reply = {
                    'objectID': util.objectid( self.request.path ),
                    'objectURI': self.request.path,
                    'parentURI': target.parent(),
                    'completionStatus': "Complete",
                    #'metadata': {},
                    'childrenrange': "0-%d" % len(children),
                    'children': children,
                }

        return ( (201,"Created"), reply )

    def get_container(self ):
        target = self.target
        try:
            children = target.list()
        except OSError, e:
            raise OperationError( 500, "unable to list directory", e )
        childrenrange = "0-%d" % len(children)
        if self.request.range:
            s, e = self.request.range
            if s is None or s < 0:
                s = 0;
            if e is None or e > len(children)-1:
                e = len(children)-1
            childrenrange = "%d-%d" % (s,e+1-s) # remember? inclusive endpoint
            children = children[s:e]

        # load user metadata here

        reply = {
                'objectID': util.objectid( self.request.path ),
                'objectURI': self.request.path,
                'parentURI': target.parent(),
                'completionStatus': "Complete",
                'metadata': {},
                'childrenrange': childrenrange,
                'children': children,
            }
        if len(self.request.fields) > 0:
            fields = self.request.fields
            for key in reply.keys():
                if key.lower() not in fields:
                    del reply[key]
        return ( (200,), reply )

    def delete_container(self ):
        target = self.target
        try:
            target.rmdir()
        except OSError, e:
            httpcode = 500
            if e.errno == 2:
                httpcode = 404
            if e.errno == 39:
                httpcode = 409
            raise OperationError( httpcode, "unable to remove directory", e );

        return ( (200,), None )

    def put_dataobject(self ):
        target = self.target
        stype, source = self.request.source

        noclobber = self.request.headers.get("X-CDMI-NoClobber", "false") # TEST
        noclobber = noclobber.strip().lower() in ("true","yes","1")

        if target.exists():
            if target.objecttype() != "dataobject" or noclobber:
                raise OperationError( 409, "path exists" )

        if stype in ("value", "rawdata"):

            if stype == "value":
                fp = StringIO( source )
                length = len(source)
            else:
                fp = self.request.fp
                length = source

            range = self.request.range
            try:
                target.write( fp, length, range )
            except (OSError, IOError), e:
                httpcode = 500
                if e.errno == 2:
                    httpcode = 404
                elif e.errno == 28:
                    httpcode = 504
                raise OperationError( httpcode, "unable to write to file", e )

        elif stype in ("move","copy","reference"):
            raise OperationError( 501, "not yet implemented", stype)

        reply = None
        if self.request.cdmi:
            reply = {
                    'objectID': util.objectid( self.request.path ),
                    'objectURI': self.request.path,
                    'parentURI': target.parent(),
                    'mimetype': "application/octet-stream",
                    'metadata': {},
                    'completionStatus': "Complete",
                }
        return ( (201,), reply )

    def get_dataobject(self ):
        pass

    def delete_dataobject(self ):
        pass



# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=79:

