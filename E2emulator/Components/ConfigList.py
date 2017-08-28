from HTMLComponent import HTMLComponent
from GUIComponent import GUIComponent
#from config import KEY_LEFT, KEY_RIGHT, KEY_HOME, KEY_END, KEY_0, KEY_DELETE, KEY_BACKSPACE, KEY_OK, KEY_TOGGLEOW, KEY_ASCII, KEY_TIMEOUT, KEY_NUMBERS, ConfigElement, ConfigText, ConfigPassword
from Components.ActionMap import NumberActionMap, ActionMap
from enigma import eListbox, eListboxPythonConfigContent, eRCInput, eTimer
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
import skin

class ConfigList(HTMLComponent, GUIComponent, object):
    def __init__(self, list, session = None):
        pass

    def execBegin(self):
        pass

    def execEnd(self):
        pass

    def toggle(self):
        pass

    def handleKey(self, key):
        pass

    def getCurrent(self):
        return 0 #rest disabled for now

    def getCurrentIndex(self):
        return 0 #rest disabled for now

    def setCurrentIndex(self, index):
        pass

    def invalidateCurrent(self):
        pass

    def invalidate(self, entry):
        pass

    GUI_WIDGET = eListbox

    def selectionChanged(self):
        pass

    def postWidgetCreate(self, instance):
        pass

    def preWidgetRemove(self, instance):
        pass

    def setList(self, l):
        pass

    def getList(self):
        return [] #rest disabled for now
        #return self.__list

    list = property(getList, setList)

    def timeout(self):
        pass

    def isChanged(self):
        is_changed = False
        return is_changed

    def pageUp(self):
        pass

    def pageDown(self):
        pass

    def selectionEnabled(self, enabled):
        pass

class ConfigListScreen:
    def __init__(self, list, session = None, on_change = None):
        pass

    def createSummary(self):
        pass

    def getCurrentEntry(self):
        return ""

    def getCurrentValue(self):
        return ""

    def getCurrentDescription(self):
        return ""

    def changedEntry(self):
        pass

    def handleInputHelpers(self):
        pass

    def KeyText(self):
        pass

    def VirtualKeyBoardCallback(self, callback = None):
        pass

    def keyOK(self):
        pass

    def keyLeft(self):
        pass

    def keyRight(self):
        pass

    def keyHome(self):
        pass

    def keyEnd(self):
        pass

    def keyDelete(self):
        pass

    def keyBackspace(self):
        pass

    def keyToggleOW(self):
        pass

    def keyGotAscii(self):
        pass

    def keyNumberGlobal(self, number):
        pass

    def keyPageDown(self):
        pass

    def keyPageUp(self):
        pass

    def keyFile(self):
        pass

    def handleKeyFileCallback(self, answer):
        pass

    def saveAll(self):
        pass

    # keySave and keyCancel are just provided in case you need them.
    # you have to call them by yourself.
    def keySave(self):
        self.saveAll()
        self.close()

    def cancelConfirm(self, result):
        if not result:
            return

        self.close()

    def closeMenuList(self, recursive = False):
        self.close(recursive)

    def keyCancel(self):
        self.closeMenuList()

    def closeRecursive(self):
        self.closeMenuList(True)