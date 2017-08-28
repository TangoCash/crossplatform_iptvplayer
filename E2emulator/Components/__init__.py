import sys
import os

E2root = os.path.dirname(os.path.realpath(sys.argv[0]))
if os.path.basename(E2root) == 'IPTVPlayer':
    E2root = os.path.dirname(E2root)
    if os.path.basename(E2root) == 'Extensions':
        E2root = os.path.dirname(E2root)
        if os.path.basename(E2root) == 'Plugins':
            E2root = os.path.dirname(E2root)
    

if E2root not in sys.path:
    sys.path.append(E2root)
