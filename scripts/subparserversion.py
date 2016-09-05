# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
import traceback

def printDBG(strDat):
    if 1:
        print("%s" % strDat)

def printExc(msg=''):
    printDBG("===============================================")
    printDBG("                   EXCEPTION                   ")
    printDBG("===============================================")
    msg = msg + ': \n%s' % traceback.format_exc()
    printDBG(msg)
    printDBG("===============================================")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Please rpovide libsPath', file=sys.stderr)
        sys.exit(1)
    try:
        libsPath = sys.argv[1]
        sys.path.insert(1, libsPath)
        from iptvsubparser import _subparser as subparser
        printDBG(subparser.version())
        sys.exit(0)
    except Exception:
        printExc()
    sys.exit(1)

