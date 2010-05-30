#!/usr/bin/env python
# Koen Bollen <meneer koenbollen nl>
# 2010 GPL

import os
import yaml

import cdmi

def main():
    path = os.path.join( os.path.dirname(__file__), "requests.yaml" )
    requests = yaml.load( open( path ) )
    for req in requests:
        print req['description']

        headers = req.get( "headers", {} )
        headers['Host'] = "localhost"
        res = cdmi.Request( req['method'], req['path'], headers )
        print res, res.fields
        print

if __name__ == "__main__":
    main()

# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=79:

