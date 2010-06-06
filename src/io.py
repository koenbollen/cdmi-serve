# Koen Bollen <meneer koenbollen nl>
# 2010 GPL
#
# TODO: Make this module threadsafe (by indepth path), very important.
#


import os

from functools import wraps

class IO( object ):

    def __init__(self, root="./" ):
        self.root = root

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

    def mkdir(self, path ):
        return os.mkdir( self.resolve( path ) )

    def stat(self, path ):
        return os.stat( self.resolve( path ) )

    def list(self, path ):
        path = self.resolve( path )
        ls = os.listdir( path )
        for i,e in enumerate(ls):
            if os.path.isdir( os.path.join( path, e ) ):
                ls[i] += "/"
        return ls


class _Wrapper( object ):
    def __init__(self, io, path ):
        self.io = io
        self.path = path

    def __getattr__(self, name ):
        # FEATURE: Cache here.
        mthd = getattr( self.io, name )
        @wraps( mthd )
        def wrapper( *args, **kwargs ):
            return mthd(self.path, *args, **kwargs )
        return wrapper


# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=79:

