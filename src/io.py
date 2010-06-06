# Koen Bollen <meneer koenbollen nl>
# 2010 GPL
#
# TODO: Make this module threadsafe (by indepth path), very important.
#


import os

from functools import wraps

DEFAULT_BUFSIZE = 64*1024

class IO( object ):

    def __init__(self, root="./", bufsize=DEFAULT_BUFSIZE ):
        self.root = root
        self.bufsize = bufsize

    def buildtarget(self, path ):
        return _Wrapper( self, path )

    def resolve(self, path ):
        path = path.replace("\\","/").lstrip("/")
        return os.path.join( self.root, path )

    def parent(self, path ):
        return os.path.dirname( path )

    def exists(self, path ):
        return os.path.exists( self.resolve(path) )

    def objecttype(self, path ):
        path = self.resolve( path )
        if os.path.isdir( path ):
            return "container"
        elif os.path.isfile( path ):
            return "dataobject"
        return "unknown"

    def stat(self, path ):
        return os.stat( self.resolve( path ) )

    def mkdir(self, path ):
        return os.mkdir( self.resolve( path ) )

    def rmdir(self, path ):
        return os.rmdir( self.resolve( path ) )

    def list(self, path ):
        path = self.resolve( path )
        ls = os.listdir( path )
        for i,e in enumerate(ls):
            if os.path.isdir( os.path.join( path, e ) ):
                ls[i] += "/"
        return ls

    def write(self, path, fp, length, range=None ):
        # important locking point.

        givenlength = length
        if range is not None and None not in range:
            length = min( length, range[1]-range[0] )

        if range is None or not self.exists(path):
            mode = "wb"
        else:
            mode = "r+b"
        out = open( self.resolve( path ), mode, self.bufsize )
        out.seek(0, os.SEEK_SET)
        if range is not None and range[0]:
            out.seek( range[0], os.SEEK_SET )

        nbytes = 0
        while nbytes < length:
            chunk = fp.read( min( length, self.bufsize ) )
            if not chunk:
                break
            out.write( chunk )
            nbytes += len(chunk)

        out.close()

        if givenlength != length:
            fp.read( givenlength - length )

class _Wrapper( object ):
    def __init__(self, io, path ):
        self.io = io
        self.path = path

    def __getattr__(self, name ):
        # FEATURE: Cache here, object bound.
        mthd = getattr( self.io, name )
        @wraps( mthd )
        def wrapper( *args, **kwargs ):
            return mthd(self.path, *args, **kwargs )
        return wrapper


# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=79:

