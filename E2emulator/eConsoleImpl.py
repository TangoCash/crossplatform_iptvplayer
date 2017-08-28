#!/usr/bin/env python

# j00zek: python poor implementaion of eConsoleImpl enigma2 code
# based on https://gist.github.com/wynemo/4343395


#usage example:
#
#pp = eConsoleImpl()
#reactor.spawnProcess(pp, "wget", 
#                     ['wget',
#                     'http://mirrors.neusoft.edu.cn/ubuntu-releases/xenial/ubuntu-16.04.1-server-amd64.template',
#                     '-O',
#                     '/dev/null',], usePTY = True)
#reactor.run()

from twisted.internet import protocol, reactor, defer
import sys

class eConsoleImpl(protocol.ProcessProtocol):
    def __init__(self):
        pass
    def connectionMade(self):
        #print "connectionMade!"
        #self.transport.closeStdin() # tell them we're done
        pass
    def outReceived(self, data):
        #print "outReceived!"
        sys.stdout.write(data)
        sys.stdout.flush()
    def errReceived(self, data):
        sys.stderr.write(data)
        sys.stderr.flush()
    def inConnectionLost(self):
        pass #print "inConnectionLost! stdin is closed! (we probably did it)"
    def outConnectionLost(self):
        pass #print "outConnectionLost! The child closed their stdout!"
    def errConnectionLost(self):
        pass #print "errConnectionLost! The child closed their stderr."
    def processExited(self, reason):
        pass #print "processExited, status %d" % (reason.value.exitCode,)
    def processEnded(self, reason):
        pass #print "processEnded, status %d" % (reason.value.exitCode,)
        reactor.stop()
