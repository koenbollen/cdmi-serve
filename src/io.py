#!/usr/bin/env python
#

import os

class IO( object ):

    def __init__(self, root="./" ):
        self.root = root

    def resolve(self, path ):
        path = path.replace("\\","/").lstrip("/")
        return os.path.join( self.root, path )

    def exists(self, path ):
        return os.path.exists( self.resolve(path) )

    def objecttype(self, path ):
        path = self.resolve( path )
        if os.path.isdir( path ):
            return "container"
        elif os.path.isfile( path ):
            return "dataobject"
        return "unknown"



# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=79:

