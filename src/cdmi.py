#!/usr/bin/env python
# Koen Bollen <meneer@koenbollen.nl>
# 2010 GPL

try:
    import json
except ImportError:
    import simplejson as json

import util


SPECIFICATION_VERSION = 1.0
DEFAULT_PORT = 2364

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
    def __init__(self, message, cause ):
        self.message = message
        self.cause = cause

    def __str__(self ):
        return "%s: %r" % (self.message, self.cause)

    def __repr__(self ):
        return "<CDMIProtocolError %s>" % (str(self))

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
                    raise ProtocolError( "unable to parse json", e )


        if not self.cdmi and self.contenttype:
            self.source = ( "rawdata", None )
        elif self.cdmi and self.method in ("post", "put"):
            if not self.json:
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
            self.range = (None, None)

    def container(self ):

        if "children" in self.fields and self.fields['children'] is not None:
            range = [int(p) for p in self.fields['children'].split("-")]
            range = (range + [None]*2)[:2]
            if range[1] is not None:
                range[1] += 1
            self.range = tuple(range)


# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=79:

