#!/usr/bin/env python
# encoding: utf-8
"""
"""

import os
import sys
from datetime import datetime 
    # recurvsively search directory
for root, dirnames, filenames in os.walk(sys.argv[1]):
    for filename in filenames:
	fpath = os.path.join(root, filename)
	fname, fdir = os.path.split(fpath)
        date = datetime.fromtimestamp(os.path.getmtime(fpath))
        print "%s, %s, %s, %s" %(fdir, fname, os.path.getsize(fpath), date)

