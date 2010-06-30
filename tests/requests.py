#!/usr/bin/env python
# Koen Bollen <meneer koenbollen nl>
# 2010 GPL

import os, sys
from pprint import pprint
import socket
import yaml
try:
    import readline
except ImportError:
    pass
import cmd

class TestShell( cmd.Cmd ):

    prompt = "cdmi test> "
    def __init__(self ):
        cmd.Cmd.__init__( self )

        self.do_reload()

        self.sock = None

        self.cfg = {
                'verbose': "0",
                'host': "localhost",
                'port': "2364",
                'continuous': "0",
            }

    def echo(self, msg ):
        try:
            if int(self.cfg.get("verbose","0")):
                print msg
        except ValueError:
            pass
    def get_connection(self ):
        if int(self.cfg.get("continuous","0")):
            return self.sock
        return socket.create_connection( (self.cfg['host'],
                int(self.cfg['port'])) )

    def close_connection(self, sock=None ):
        if not int(self.cfg.get("continuous","0")):
            sock.close()

    def reset_connection(self ):
        if int(self.cfg.get("continuous","0")):
            if self.sock:
                self.sock.close()
            self.sock = socket.create_connection( (self.cfg['host'],
                int(self.cfg['port'])) )

    def do_set(self, line ):
        """Modify, read or list settings."""
        if not line:
            for k,v in self.cfg.items():
                print k, "=", v
            return
        try:
            key, value = line.split("=", 1)
        except ValueError:
            key = line.strip().lower()
            if key in self.cfg:
                print key, "=", self.cfg.get(key)
        else:
            self.cfg[key.strip().lower()] = value.strip()

    def do_list(self, line ):
        """List availible requests."""
        for i, req in enumerate(self.requests):
            print "%d) %s" %(i+1, req['description'])

    def do_reload(self, line=None ):
        """Reload the requests yaml database."""
        path = os.path.join( os.path.dirname(__file__), "requests.yaml" )
        with open( path) as fp:
            self.requests = yaml.load(fp)

        self.commands = {}
        for req in self.requests:
            if "command" in req:
                name = req['command']['name']
                self.commands[name] = req

    def do_run(self, line ):
        """Runs a test from the `list' command."""
        line = line.replace(",", " ").split()
        todo = []

        for i in line:
            try:
                todo.append( int( i ) - 1 )
            except ValueError:
                continue

        if len(todo) < 1:
            print "invalid selection"
            return

        self.reset_connection()

        for i in todo:
            req = self.requests[i]
            self.run( req )

    def do_print(self, line ):
        pprint( self.requests[int(line)-1] )

    def run(self, req ):
        headers = req.get( "headers", {} )
        headers['Host'] = self.cfg['host']

        data = req.get( "data" )
        if data:
            data = data.strip()+"\n"
            data = data.replace( "\r", "" ).replace( "\n", "\r\n" )
            headers['Content-Length'] = len(data)

        s = self.get_connection()
        bytes = "%s %s HTTP/1.1\r\n" % ( req['method'], req['path'] )
        self.echo( "> "+bytes.strip() )
        s.send( bytes )
        for header in headers.items():
            bytes = "%s: %s\r\n" % header
            self.echo( "> "+bytes.strip() )
            s.send( bytes )
        self.echo( ">" )
        s.send( "\r\n" )

        if data:
            self.echo( "> "+data.strip().replace( "\n", "\n> " ) )
            s.send( data )

        while True:
            try:
                d = s.recv( 1024 )
            except socket.timeout:
                break
            if not d:
                break
            print d,
        print
        self.close_connection( s )

    def default(self, line ):
        try:
            command, args = line.split(None, 1)
        except ValueError:
            command = line.strip()
            args = ""
        if command not in self.commands:
            print "*** Unknown syntax:", line
            return
        req = self.commands[command]
        a = req['command']['args']
        if len(a) > 0:
            args = args.split()
            for i, arg in enumerate(args):
                req[a[i]] = arg
        self.run( req )

def main():
    socket.setdefaulttimeout( 1 )
    sh = TestShell()
    try:
        sh.cmdloop()
    except KeyboardInterrupt:
        print "quit"

if __name__ == "__main__":
    main()

# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=79:

