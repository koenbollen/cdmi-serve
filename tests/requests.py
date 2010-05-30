#!/usr/bin/env python
# Koen Bollen <meneer koenbollen nl>
# 2010 GPL

import os
from StringIO import StringIO
import yaml

import cdmi

def main():
    path = os.path.join( os.path.dirname(__file__), "requests.yaml" )
    requests = yaml.load( open( path ) )
    for req in requests:
        print req['description']

        headers = req.get( "headers", {} )
        headers['Host'] = "localhost"

        data = req.get( "data" )
        if data:
            data = data.strip()+"\n"
            data = data.replace( "\r", "" ).replace( "\n", "\r\n" )
            headers['Content-Length'] = len(data)
        res = cdmi.Request( req['method'], req['path'], headers )
        if res.expects and data:
            res.read( StringIO( data ) )
        res.phase2()
        print res, res.fields, res.source
        print


if __name__ == "__main__":
    main()

# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=79:

