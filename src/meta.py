# Koen Bollen <meneer koenbollen nl>
# 2010 GPL
#
# TODO: Make this module threadsafe.
#

import sys
import cPickle as pickle


class Meta( object ):

    debug = False

    def __init__(self, dbtype, dbconnect ):

        try:
            self.dba = __import__( dbtype )
        except ImportError:
            print >>sys.stderr, "unable to load %r, please install" % dbtype
        self.dbc = self.dba.connect( dbconnect )
        if self.debug: print "meta: connected"

        c = self.dbc.cursor()

        sql  = "CREATE TABLE IF NOT EXISTS objects (\n"
        sql += "  objectid UNIQUE NOT NULL,\n"
        sql += "  mimetype NULL, metadata )\n"
        if self.debug: print "meta: %r"%sql
        c.execute( sql )

        self.dbc.commit()

    def set(self, objectid, *args ):

        metadata = None
        mimetype = None
        for arg in args:
            if isinstance( arg, dict ):
                metadata = arg
            elif isinstance( arg, str ) or isinstance( arg, unicode ):
                mimetype = arg
            elif arg is not None:
                raise ValueError( "invalid argument: %r" % arg )
            if None not in (metadata, mimetype):
                break

        if metadata is None:
            metadata = {}

        data = pickle.dumps( metadata )

        c = self.dbc.cursor()

        sql = "INSERT OR REPLACE INTO objects VALUES (?, ?, ?)"
        if self.debug: print "meta: %r"%sql
        c.execute( sql, (objectid, mimetype, data ) )

        self.dbc.commit()

    def update(self, objectid, *args ):

        metadata = None
        mimetype = None
        for arg in args:
            if isinstance( arg, dict ):
                metadata = arg
            elif isinstance( arg, str ) or isinstance( arg, unicode ):
                mimetype = arg
            elif arg is not None:
                raise ValueError( "invalid argument: %r" % arg )
            if None not in (metadata, mimetype):
                break

        try:
            mime, meta = self.get( objectid )
        except KeyError:
            self.set( objectid, *args )
            return mimetype, metadata
        if mimetype is not None:
            mime = mimetype
        if metadata is not None:
            meta.update( metadata )

        args = [ meta ]
        if mime:
            args.append( mime )
        self.set( objectid, *args )
        return mime, meta

    def get(self, objectid ):

        if not objectid:
            raise ValueError( "invalid objectid: %r" % objectid )

        c = self.dbc.cursor()

        sql  = "SELECT mimetype, metadata FROM objects\n"
        sql += "WHERE objectid = ?\n"
        if self.debug: print "meta: %r"%sql
        c.execute( sql, ( objectid, ) )

        row = c.fetchone()
        if not row:
            raise KeyError( objectid )
        mime, meta = row[:2]

        if mime is not None:
            mime = mime.encode( "ascii" )

        return mime, pickle.loads( meta.encode( "ascii" ) )

    def delete(self, objectid ):

        if not objectid:
            raise ValueError( "invalid objectid: %r" % objectid )

        c = self.dbc.cursor()

        sql  = "DELETE FROM objects\n"
        sql += "WHERE objectid = ?\n"
        if self.debug: print "meta: %r"%sql
        c.execute( sql, ( objectid, ) )

        self.dbc.commit()


def test():
    a = Meta( "sqlite3", ":memory:" )

    try:   print a.get( "13" )
    except KeyError: pass
    else:  print "no KeyError"
    try:   print a.get( "" )
    except ValueError:        pass
    else:  print "no ValueError"
    try:   a.set( "11", 1 )
    except ValueError:        pass
    else:  print "no ValueError"

    a.set( "d42", { 'size': 4, 'value': "Koen"} )
    a.update( "d42", {'extra': "cool!"} )
    assert a.get( "d42" ) == (None, {'size': 4, 'value': 'Koen', 'extra': 'cool!'})
    a.set( "d42", { 'size': 3, 'value': "sup"} )
    assert a.get( "d42" ) == (None, {'value': 'sup', 'size': 3})
    a.delete( "d42" )
    a.delete( "d42" )
    try:   print a.get( "d42" )
    except KeyError: pass
    else:  print "no KeyError"

    a.set( "14", "image/png", {'size': 4} )
    assert a.get("14") == ('image/png', {'size': 4})
    a.set( "15", {'size': 5}, "text/plain" )
    assert a.get("15") == ('text/plain', {'size': 5})
    a.update( "15", "text/json" )
    assert a.get("15") == ('text/json', {'size': 5})
    a.set( "16" )
    assert a.get("16") == (None, {})

    a.update( "17", {'project': 'mine'} )
    assert a.get("17") == (None, {'project': 'mine'})

if __name__ == "__main__":
    test()

# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=79:
