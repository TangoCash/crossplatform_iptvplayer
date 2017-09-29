import sys
import os
from tempfile import gettempdir

E2root = os.path.dirname(os.path.realpath(sys.argv[0]))
if os.path.basename(E2root) == 'IPTVPlayer':
    E2root = os.path.dirname(E2root)
    if os.path.basename(E2root) == 'Extensions':
        E2root = os.path.dirname(E2root)
        if os.path.basename(E2root) == 'Plugins':
            E2root = os.path.dirname(E2root)
   

if E2root not in sys.path:
    sys.path.append(E2root)

def getSysTempFolder():
    ret = None
    envTemps=('KODI_TEMP', 'TMP', 'TEMP')
    for envSetting in envTemps:
        if envSetting in os.environ:
            if os.path.exists(os.environ[envSetting]) and os.access(os.environ[envSetting], os.W_OK):
                ret = os.environ[envSetting]
                break
    if ret is None:
        if 'ANDROID_ROOT' in os.environ or 'ANDROID_DATA' in os.environ:
            for TP in ['/storage/sdcard1', '/storage/sda1/', '/data/local/tmp/', '/storage/emulated/0/tmp/', '/tmp' ]:
                if os.path.exists(TP) and os.access(TP, os.W_OK):
                    ret = TP
                    break
            if ret is None: # when no path found for shitty Android...
                ret = '/Android_Fake_Temp_Path' # we set it to something usefull for debug logs
        else:
            ret = gettempdir()
    return ret
