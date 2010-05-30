#!/usr/bin/env python
#

import cPickle as pickle

class Access( object ):

    def __init__(self, dbtype, dbconnect, verbose=False ):
        self.verbose = verbose
        self.dba = __import__( dbtype )
        self.dbc = self.dba.connect( dbconnect )

        c = self.dbc.cursor()
        sql  = "CREATE TABLE IF NOT EXISTS objects (\n"
        sql += "  objectid UNIQUE NOT NULL,\n"
        sql += "  path NOT NULL,\n  metadata,\n"
        sql += "  UNIQUE ( objectid, path ) )\n"
        if self.verbose: print sql
        c.execute( sql )
        self.dbc.commit()

    def set(self, objectid, path, metadata ):
        c = self.dbc.cursor()
        sql = "INSERT OR REPLACE INTO objects VALUES (?, ?, ?)"
        if self.verbose: print sql
        c.execute( sql, (objectid, path, pickle.dumps( metadata )) )
        self.dbc.commit()
        return True

    def update(self, objectid, metadata ):
        current = self.get( objectid )
        if not current:
            return False
        current['metadata'].update( metadata )
        return self.set( objectid, current['path'], current['metadata'] )

    def lookup(self, path ):
        c = self.dbc.cursor()
        sql = "SELECT objectid FROM objects WHERE path = ?"
        if self.verbose: print sql
        c.execute( sql, ( path, ) )
        row = c.fetchone()
        if not row:
            return None
        return row[0]

    def get(self, objectid ):
        c = self.dbc.cursor()
        sql  = "SELECT objectid, path, metadata FROM objects\n"
        sql += "WHERE objectid = ?\n"
        if self.verbose: print sql
        c.execute( sql, ( objectid, ) )
        row = c.fetchone()
        if not row:
            return None
        return {
                'path': row[0],
                'objectid': row[1],
                'metadata': pickle.loads( row[2].encode( "ascii" ) )
            }


def test():
    a = Access( "sqlite3", ":memory:", True )
    a.set( "42", "/mydata", { 'size': 4, 'value': "Koen"} )
    a.update( "42", {'extra': "cool!"} )
    print a.get( "42" )
    a.set( "42", "/mydata", { 'size': 3, 'value': "sup"} )
    a.set( "42", "/mydata", { 'size': 3, 'value': "sup"} )
    print a.get( a.lookup( "/mydata" ) )
    a.set( "42", "/a", { 'size': 0 } )
    print a.get( "42" )
    print a.get( "13" )

if __name__ == "__main__":
    test()

# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=79:

