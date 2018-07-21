import sys
import os

E2root = os.path.dirname(os.path.realpath(sys.argv[0])).replace("/Plugins/Extensions/IPTVPlayer","")

if E2root not in sys.path:
    sys.path.append(E2root)
