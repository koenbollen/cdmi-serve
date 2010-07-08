# Koen Bollen <meneer koenbollen nl>
# 2010 GPL

import os
from functools import wraps
import threading

import mimetypes
try:
    import cPickle as pickle
except ImportError:
    import pickle

DEFAULT_BUFSIZE = 64*1024
METAFILE_PREFIX = ".metafile-"

class IO( object ):

    def __init__(self, root="./", bufsize=DEFAULT_BUFSIZE ):
        self.root = root
        self.bufsize = bufsize

        self.locks = {}

        if not mimetypes.inited:
            mimetypes.init( mimetypes.knownfiles )

    def __acquire(self, path ):
        #print "acquiring lock:", path
        if path not in self.locks:
            self.locks[path] = threading.Lock()
        self.locks[path].acquire()

    def __release(self, path ):
        #print "releasing lock:", path
        if path not in self.locks:
            self.locks[path] = threading.Lock()
        self.locks[path].release()

    def buildtarget(self, path ):
        return _Curry( self, path )

    def resolve(self, path ):
        path = path.replace("\\","/").lstrip("/")
        return os.path.join( self.root, path )

    def metafile(self, path ):
        path = os.path.normpath( path )
        sep = "/"+METAFILE_PREFIX
        if path == "/":
            return self.resolve( sep+"ROOT" )
        return self.resolve( sep.join( os.path.split( path ) ) )

    def parent(self, path ):
        return os.path.dirname( path.rstrip("/") )

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
        try:
            os.unlink( self.metafile( path ) )
        except OSError, (errno, errstr):
            if errno != 2:
                raise
        return os.rmdir( self.resolve( path ) )

    def rename( self, path, source ):
        self.__acquire( source )
        self.__acquire( path )
        try:
            result = os.rename( self.resolve(source), self.resolve(path) )
            try:
                os.rename( self.metafile(source), self.metafile(path) )
            except OSError, (errno, errstr):
                if errno != 2:
                    raise
            return result
        finally:
            self.__release( path )
            self.__release( source )

    def list(self, path ):
        path = self.resolve( path )
        ls = os.listdir( path )
        ls = filter( lambda x: not x.startswith( METAFILE_PREFIX ), ls )
        for i,e in enumerate(ls):
            if os.path.isdir( os.path.join( path, e ) ):
                ls[i] += "/"
        return ls

    def write(self, path, fp, length, offset=None ):
        self.__acquire( path )

        if offset is None or not self.exists(path):
            mode = "wb"
        else:
            mode = "r+b"
        try:
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
            return nbytes
        finally:
            self.__release( path )

    def read(self, path, length, offset=None ):
        self.__acquire( path )

        s = self.stat( path )
        size = s.st_size
        if offset is not None:
            if offset > size:
                offset = size
            length = min(length, size - offset)
        else:
            length = min(length, size)

        try:
            f = open( self.resolve(path), "rb", self.bufsize )
            try:
                if offset:
                    f.seek( offset, os.SEEK_SET )
                value = f.read( length )
            finally:
                f.close()
            return value
        finally:
            self.__release( path )

    def open(self, path, mode="rb" ):
        self.__acquire( path )
        try:
            fp = _ControlledFile( self.resolve(path), mode, self.bufsize )
            fp.io = self
            fp.path = path
        except:
            self.__release( path )
            raise
        return fp

    def close(self, path ):
        self.__release( path )

    def unlink(self, path ):
        self.__acquire( path )
        try:
            res = os.unlink( self.resolve( path ) )
            try:
                os.unlink( self.metafile( path ) )
            except OSError, (errno, errstr):
                if errno != 2:
                    raise
            return res
        finally:
            self.__release( path )

    def mime(self, path ):
        self.__acquire( path )
        try:
            res = mimetypes.guess_type( self.resolve(path) )
            try:
                type, enc = res
            except ValueError:
                type = res
            if not type:
                type = "application/octet-stream"
            return type
        finally:
            self.__release( path )

    def meta(self, path, data=None, overwrite=False ):
        self.__acquire( path )

        try:
            metafile = self.metafile(path)

            if data is None and overwrite:
                os.unlink( metafile )
                return {}

            if not overwrite:
                try:
                    fp = open( metafile, "rb" )
                except IOError, (errno, errstr):
                    if errno != 2:
                        raise
                    metadata = {}
                else:
                    metadata = pickle.load( fp )
                    fp.close()
                if data is not None:
                    metadata.update( data )
            elif data is not None:
                metadata = data

            if data is not None:
                fp = open( metafile, "wb" )
                pickle.dump( metadata, fp, -1 )
                fp.close()

            return metadata
        finally:
            self.__release( path )



class _ControlledFile( file ):
    def close(self ):
        self.io.close( self.path )
        file.close( self )

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

