# helper module that enables this project to run without installing.
# Koen Bollen <meneer koenbollen nl>
# 2010 GPL

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname( __file__ )) )
from src import *

# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=79:

