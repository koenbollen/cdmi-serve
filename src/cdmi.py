#!/usr/bin/env python
# Koen Bollen <meneer@koenbollen.nl>
# 2010 GPL

SPECIFICATION_VERSION = 1.0

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

class CDMIProtocolError( CDMIError ):
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
        self.json = None

        self.__validate()
        self.__parse()

    def __validate(self ):
        if self.method not in ("get", "post", "put", "delete"):
            raise CDMIProtocolError( "invalid method:", self.method )
        if self.path[0] != '/':
            raise CDMIProtocolError( "invalid path", self.path )

    def __parse(self ):
        h = self.headers
        spec = h.get('X-CDMI-Specification-Version')
        self.cdmi = spec is not None
        if self.cdmi:

            try:
                if float(spec) < SPECIFICATION_VERSION:
                    raise ValueError
            except ValueError:
                raise CDMIProtocolError( "incorrect version", spec )

            try:
                accept = h['Accept']
                contenttype = h['Content-Type']
            except KeyError, e:
                # One exception, a GET request without a type:
                if not (e.args[0].lower() == "accept" and self.method=="get"):
                    raise CDMIProtocolError( "missing header", str(e) )
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

        p = self.path
        self.fields = {}
        if "?" in self.path:
            self.path, fstr = self.path.split( "?", 1 )
            fields = [(f.split(":", 1)+[None])[:2] for f in fstr.split(";")]
            for k,v in fields:
                if v:
                    v = v.strip()
                self.fields[k.strip().lower()] = v

    def __repr__(self ):
        tmpl = "<cdmi request: {cdmi} {method} a {objecttype}: '{path}'>"
        values = vars(self)
        values['cdmi'] = self.cdmi and "cdmi" or "non-cdmi"
        return tmpl.format( **values )

    def read(self, fp ):
        pass

# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=79:

