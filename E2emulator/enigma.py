# -*- coding: utf-8 -*-
#
# This is fake enigma file
# do whatever you need with it.
#

import os
from eConsoleImpl import eConsoleImpl
from twisted.internet import reactor, defer

class eConsoleAppContainer():
    m_cwd=""
    def setCWD(self, myPath): #int setCWD( const char *path );
        if not os.path.exists(myPath):
            return -1
        elif os.path.isfile(myPath):
            return -2
        else:
            self.m_cwd=myPath
            return 0

    def kill(self): #void kill();
        #reactor.stop() ????
        pass

    def sendCtrlC(self): #void sendCtrlC();
        self.kill()

    def sendEOF(self): #void sendEOF();
        self.kill()

    def appClosed(self, retval): #PSignal1<void,int> appClosed;
        pass
    
    def stderrAvail(self, str): #PSignal1<void, const char*> stderrAvail;
        pass
    
    def dataSent(self): #PSignal1<void,int> dataSent;
        pass

    def stdoutAvail(self, str): #PSignal1<void, const char*> stdoutAvail;
        pass

    def dataAvail(self, str): #PSignal1<void, const char*> dataAvail;
        pass

    def write(self, str): #void write( const char *data, int len );
        pass

    def setFileFD(self, str): #void setFileFD(int num, int fd) { if (num >= 0 && num <= 2) filefd[num] = fd; }
        pass

    def running(self, str): #bool running() { return (fd[0]!=-1) && (fd[1]!=-1) && (fd[2]!=-1); }
        pass

    def execute(self,cmdlineSRC): #int execute( const char *cmdline, const char *const argv[] );
        isWget = False
        #print cmdlineSRC
        #FNULL = open(os.devnull, 'w')
        if not isinstance(cmdlineSRC, basestring):
            cmdParameters=cmdline
        else:
            print "isLine"
            cmdline=cmdlineSRC.replace('> /dev/null','').strip() #remove /dev/null, it's not crossplatform
            cmdParameters=cmdline.split(" ")
            
        print cmdParameters
        if 'wget' in cmdParameters:
            isWget = True
        else:
            for param in cmdParameters:
                if str(param).find('wget') >0:
                    isWget = True
                    
        if isWget == True: #for wget separate process and logs
            TempPath = None
            try:
                TempPath = os.path.join(Components.config.config.misc.sysTempPath.value,'.IPTVdaemon')
            except:
                from initSysPaths import getSysTempFolder
                TempPath = getSysTempFolder()
                
            if TempPath is None:
                raise ValueError('EXCEPTION!!! System temp path NOT found!!!')
            elif not os.path.exists(TempPath):
                raise ValueError('EXCEPTION!!! System temp path (%s) does NOT exist!!!' % TempPath)
            elif not os.access(TempPath, os.W_OK):
                raise ValueError('EXCEPTION!!! System temp path (%s) is NOT writable!!!' % TempPath)
                
            iindex = 1
            FNULLfileName = '/dev/null'
            if cmdline.find(' -O ') >= 0: #each wget contains own log
                fileName = cmdline[cmdline.find(' -O ')+len(' -O '):].replace('"','').strip()
                try:
                    FNULLfileName = '%s.wget' % fileName
                    FNULL = open(FNULLfileName, 'w') #try to open it to check if it's blocked or not e.g. another process is downloading the file atm
                    if FNULL:
                        FNULL.close()
                except:
                    while True:
                        if not os.path.exists(os.path.join(TempPath,'wget%d.log' % iindex)):
                            break
                        iindex += 1
                    FNULLfileName = os.path.join(TempPath,'wget%d.log') % iindex
            else:
                FNULLfileName = os.path.join(TempPath,'eConsole.log')
                
            try:
                from subprocess import Popen
                FNULL = open(FNULLfileName, 'w')
                Popen(cmdline, stdout=FNULL, stderr=FNULL, shell=True)
            except Exception: #another workarround for Android :P
                if FNULL:
                    FNULL.close()
                if os.path.exists(FNULLfileName) and FNULLfileName != '/dev/null':
                    os.remove(FNULLfileName)
                os.system('( %s >"%s" 2>&1 ) &' % (cmdline,FNULLfileName) )
                
            return
        else:
            myConsole = eConsoleImpl()
            try:
                reactor.spawnProcess(myConsole, cmdParameters[0], cmdParameters, path = self.m_cwd, usePTY = True)
                reactor.run()
            except Exception, e:
                print 'Exception (%s) starting reactor' % str(e)

# fake-enigma from openpli github

import fake_time

class slot:
    def __init__(self):
        self.list = [ ]

    def get(self):
        return self.list

    def __call__(self):
        for x in self.list:
            x()

timers = set()

import time

from events import eventfnc

##################### ENIGMA BASE

class eTimer:
    def __init__(self):
        self.timeout = slot()
        self.next_activation = None
        print "NEW TIMER"

    def start(self, msec, singleshot = False):
        print "start timer", msec
        self.next_activation = time.time() + msec / 1000.0
        self.msec = msec
        self.singleshot = singleshot
        timers.add(self)

    def stop(self):
        timers.remove(self)

    def __repr__(self):
        return "<eTimer timeout=%s next_activation=%s singleshot=%s>" % (repr(self.timeout), repr(self.next_activation), repr(self.singleshot))

    def do(self):
        if self.singleshot:
            self.stop()
        self.next_activation += self.msec / 1000.0
        self.timeout()

def runIteration():
    running_timers = list(timers)
    assert len(running_timers), "no running timers, so nothing will ever happen!"
    running_timers.sort(key=lambda x: x.next_activation)

    print "running:", running_timers

    next_timer = running_timers[0]

    now = time.time()
    delay = next_timer.next_activation - now

    if delay > 0:
        time.sleep(delay)
        now += delay

    while len(running_timers) and running_timers[0].next_activation <= now:
        running_timers[0].do()
        running_timers = running_timers[1:]

stopped = False

def stop():
    global stopped
    stopped = True

def run(duration = 1000):
    stoptimer = eTimer()
    stoptimer.start(duration * 1000.0)
    stoptimer.callback.append(stop)
    while not stopped:
        runIteration()


##################### ENIGMA GUI

eButton = None

eListbox = None
eListboxPythonConfigContent = None
eListboxPythonMultiContent = None
eListboxPythonStringContent = None

eSize = None
ePoint = None
gFont = None

eWindow = None
eWindowStyleManager = None
eWindowStyleSkinned = None

eLabel = None
ePixmap = None
loadPNG = None
addFont = None
gRGB = None
eSubtitleWidget = None
RT_HALIGN_LEFT = None
RT_HALIGN_RIGHT = None
RT_HALIGN_CENTER = None
RT_VALIGN_CENTER = None
getDesktop = None

class eEPGCache:
    @classmethod
    def getInstance(self):
        return self.instance

    instance = None

    def __init__(self):
        eEPGCache.instance = self

    def lookupEventTime(self, ref, query):
        return None

eEPGCache()

getBestPlayableServiceReference = None

class pNavigation:
    def __init__(self):
        self.m_event = slot()
        self.m_record_event = slot()

    @eventfnc
    def recordService(self, service):
        return iRecordableService(service)

    @eventfnc
    def stopRecordService(self, service):
        service.stop()

    @eventfnc
    def playService(self, service):
        return None

    def __repr__(self):
        return "pNavigation"

eRCInput = None
getPrevAsciiCode = None

class eServiceReference:

    isDirectory=1
    mustDescent=2
    canDescent=4
    flagDirectory=isDirectory|mustDescent|canDescent
    shouldSort=8
    hasSortKey=16
    sort1=32
    isMarker=64
    isGroup=128

    def __init__(self, ref):
        self.ref = ref
        self.flags = 0

    def toString(self):
        return self.ref

    def __repr__(self):
        return self.toString()

class iRecordableService:
    def __init__(self, ref):
        self.ref = ref

    @eventfnc
    def prepare(self, filename, begin, end, event_id):
        return 0

    @eventfnc
    def start(self):
        return 0

    @eventfnc
    def stop(self):
        return 0

    def __repr__(self):
        return "iRecordableService(%s)" % repr(self.ref)

quitMainloop = None

class eAVSwitch:
    @classmethod
    def getInstance(self):
        return self.instance

    instance = None

    def __init__(self):
        eAVSwitch.instance = self

    def setColorFormat(self, value):
        print "[eAVSwitch] color format set to %d" % value

    def setAspectRatio(self, value):
        print "[eAVSwitch] aspect ratio set to %d" % value

    def setWSS(self, value):
        print "[eAVSwitch] wss set to %d" % value

    def setSlowblank(self, value):
        print "[eAVSwitch] wss set to %d" % value

    def setVideomode(self, value):
        print "[eAVSwitch] wss set to %d" % value

    def setInput(self, value):
        print "[eAVSwitch] wss set to %d" % value

eAVSwitch()

eDVBVolumecontrol = None

class eRFmod:
    @classmethod
    def getInstance(self):
        return self.instance

    instance = None

    def __init__(self):
        eRFmod.instance = self

    def setFunction(self, value):
        print "[eRFmod] set function to %d" % value

    def setTestmode(self, value):
        print "[eRFmod] set testmode to %d" % value

    def setSoundFunction(self, value):
        print "[eRFmod] set sound function to %d" % value

    def setSoundCarrier(self, value):
        print "[eRFmod] set sound carrier to %d" % value

    def setChannel(self, value):
        print "[eRFmod] set channel to %d" % value

    def setFinetune(self, value):
        print "[eRFmod] set finetune to %d" % value

eRFmod()


class eDBoxLCD:
    @classmethod
    def getInstance(self):
        return self.instance

    instance = None

    def __init__(self):
        eDBoxLCD.instance = self

    def setLCDBrightness(self, value):
        print "[eDBoxLCD] set brightness to %d" % value

    def setLCDContrast(self, value):
        print "[eDBoxLCD] set contrast to %d" % value

    def setInverted(self, value):
        print "[eDBoxLCD] set inverted to %d" % value

eDBoxLCD();

Misc_Options = None

class eServiceCenter:
    @classmethod
    def getInstance(self):
        return self.instance

    instance = None

    def __init__(self):
        eServiceCenter.instance = self

    def info(self, ref):
        return None

eServiceCenter()

##################### ENIGMA CONFIG

print "import config"
import Components.config
print "done"

my_config = [
"config.skin.primary_skin=None\n"
]

Components.config.config.unpickle(my_config)

##################### ENIGMA ACTIONS

class eActionMap:
    def __init__(self):
        pass


##################### ENIGMA STARTUP:

def init_nav():
    print "init nav"
    import Navigation, NavigationInstance
    NavigationInstance.instance = Navigation.Navigation()

def init_record_config():
    print "init recording"
    import Components.RecordingConfig
    Components.RecordingConfig.InitRecordingConfig()

def init_parental_control():
    print "init parental"
    from Components.ParentalControl import InitParentalControl
    InitParentalControl()

def init_all():
    # this is stuff from mytest.py
    init_nav()

    init_record_config()
    init_parental_control()

    import Components.InputDevice
    Components.InputDevice.InitInputDevices()

    import Components.AVSwitch
    Components.AVSwitch.InitAVSwitch()

    import Components.UsageConfig
    Components.UsageConfig.InitUsageConfig()

    import Components.Network
    Components.Network.InitNetwork()

    import Components.Lcd
    Components.Lcd.InitLcd()

    import Components.SetupDevices
    Components.SetupDevices.InitSetupDevices()

    import Components.RFmod
    Components.RFmod.InitRFmod()

    import Screens.Ci
    Screens.Ci.InitCiConfig()
