#!/usr/bin/env python
# Koen Bollen <meneer koenbollen nl>
# 2010 GPL

from distutils.core import setup

setup(
        name = "cdmi-serve",
        version = "0.0",
        description = "A CDMI Reference Server",
        long_description= "Serve files from a local filesystem using the CDMI protocol, a CDMI server.",

        author = "Koen Bollen",
        author_email = "meneer@koenbollen.nl",
        url = "http://github.com/koenbollen/cdmi-serve",
        license = "GPL",
        platforms = [ "linux" ],

        package_dir = { 'cdmiserve': "src/" },
        packages = [ "cdmiserve" ],

        scripts = [ "scripts/cdmi-serve" ],
    )

# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=79:

