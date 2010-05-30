#!/usr/bin/env python
#

import os

class IO( object ):

    def __init__(self, root="./" ):
        self.root = root

    def join(self, path ):
        return os.path.join( self.root, path )

    def exists(self, path ):
        return os.path.exists( self.join(path) )

    def objecttype(self, path ):
        path = self.join( path )
        if os.path.isdir( path ):
            return "container"
        elif os.path.isfile( path ):
            return "dataobject"
        return "unknown"



# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=79:

