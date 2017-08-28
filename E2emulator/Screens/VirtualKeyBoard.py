# -*- coding: UTF-8 -*-
from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_CENTER, RT_VALIGN_CENTER, getPrevAsciiCode
from Screen import Screen
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN
from Tools.LoadPixmap import LoadPixmap
import skin

class VirtualKeyBoardEntryComponent:
    pass

class VirtualKeyBoard(Screen):

    def __init__(self, session, title="", **kwargs):
        Screen.__init__(self, session)
        self.setTitle(_("Virtual keyboard"))
        self.keys_list = []
        self.shiftkeys_list = []
        self.lang = language.getLanguage()
        self.nextLang = None
        self.shiftMode = False
        self.selectedKey = 0
        self.onExecBegin.append(self.setKeyboardModeAscii)
        self.onLayoutFinish.append(self.buildVirtualKeyBoard)
        self.onClose.append(self.__onClose)

    def __onClose(self):
        pass

    def switchLang(self):
        pass

    def setLang(self):
        pass

    def virtualKeyBoardEntryComponent(self, keys):
        res = [keys]
        text = []
        return res + text

    def buildVirtualKeyBoard(self):
        pass

    def markSelectedKey(self):
        pass

    def backClicked(self):
        pass

    def forwardClicked(self):
        pass

    def shiftClicked(self):
        pass

    def okClicked(self):
        pass

    def ok(self):
        pass

    def exit(self):
        self.close(None)

    def cursorRight(self):
        pass

    def cursorLeft(self):
        pass

    def left(self):
        self.smsChar = None

    def right(self):
        self.smsChar = None

    def up(self):
        self.smsChar = None

    def down(self):
        self.smsChar = None

    def keyNumberGlobal(self, number):
        pass

    def smsOK(self):
        pass

    def keyGotAscii(self):
        pass

    def selectAsciiKey(self, char):
        return False