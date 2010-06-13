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
        return _Curry( self, path )

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

    def rename( self, path, source ):
        print "rename", source, "=>", path
        return os.rename( self.resolve(source), self.resolve(path) )

    def list(self, path ):
        path = self.resolve( path )
        ls = os.listdir( path )
        for i,e in enumerate(ls):
            if os.path.isdir( os.path.join( path, e ) ):
                ls[i] += "/"
        return ls

    def write(self, path, fp, length, offset=None ):
        # important locking point.

        if offset is None or not self.exists(path):
            mode = "wb"
        else:
            mode = "r+b"
        out = open( self.resolve( path ), mode, self.bufsize )
        out.seek(0, os.SEEK_SET)
        if offset:
            out.seek( offset, os.SEEK_SET )

        nbytes = 0
        while nbytes < length:
            chunk = fp.read( min( length-nbytes, self.bufsize ) )
            if not chunk:
                break
            out.write( chunk )
            nbytes += len(chunk)

        out.close()

    def read(self, path, length, offset=None ):
        f = open( self.resolve(path), "rb", self.bufsize )
        try:
            if offset:
                f.seek( offset, os.SEEK_SET )
            value = f.read( length )
        finally:
            f.close()
        return value

    def open(self, path, mode="rb" ):
        # TODO: Figure out howto handle the close in this class
        return open( self.resolve(path), mode, self.bufsize )

    def unlink(self, path ):
        return os.unlink( self.resolve( path ) )


class _Curry( object ):
    def __init__(self, io, path ):
        self.io = io
        self.path = path

    def __getattr__(self, name ):
        # FEATURE: Cache here, object bound.
        mthd = getattr( self.io, name )
        @wraps( mthd )
        def curried( *args, **kwargs ):
            return mthd(self.path, *args, **kwargs )
        curried.__name__ += "-curried"
        return curried


# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=79:

