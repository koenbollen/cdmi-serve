#!/usr/bin/env python
# Koen Bollen <meneer koenbollen nl>
# 2010 GPL

import os, sys
import socket
import yaml

def main():
    path = os.path.join( os.path.dirname(__file__), "requests.yaml" )
    requests = yaml.load( open( path ) )

    try:
        verbose = sys.argv.index("-v")
        sys.argv.pop(verbose)
    except ValueError:
        verbose = False

    if len(sys.argv) > 1:
        r = " ".join( sys.argv[1:] )
    else:
        for i, req in enumerate(requests):
            print "%d) %s" %(i+1, req['description'])
        print "a) All"
        print "q) Quit"
        print
        r = raw_input( "Request to send? " )
    if r.strip().lower() == "q":
        sys.exit()
    if r.strip().lower() == "a":
        todo = range( len(requests) )
    else:
        r = r.replace(",", " ").split()
        todo = []
        for i in r:
            try:
                todo.append( int( i ) - 1 )
            except ValueError:
                continue
        if len(todo) < 1:
            print "invalid selection"
            sys.exit()

    socket.setdefaulttimeout( 1 )

    for i in todo:
        try:
            req = requests[i]
        except IndexError:
            continue

        print "\n" + ("-"*20) + "\nRequesting:", req['description'], "\n"

        headers = req.get( "headers", {} )
        headers['Host'] = "localhost"

        data = req.get( "data" )
        if data:
            data = data.strip()+"\n"
            data = data.replace( "\r", "" ).replace( "\n", "\r\n" )
            headers['Content-Length'] = len(data)

        s = socket.create_connection( ('localhost', 2364) )
        line = "%s %s HTTP/1.1\r\n" % ( req['method'], req['path'] )
        if verbose: print ">", line,
        s.send( line )
        for header in headers.items():
            line = "%s: %s\r\n" % header
            if verbose:
                print ">", line,
            s.send( line )
        if verbose: print ">"
        s.send( "\r\n" )
        if data:
            if verbose:
                print ">", data.strip().replace( "\n", "\n> " )
            s.send( data )

        while True:
            try:
                d = s.recv( 1024 )
            except socket.timeout:
                break
            if not d:
                break
            print d,

        s.close()

    print

if __name__ == "__main__":
    main()

# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=79:

