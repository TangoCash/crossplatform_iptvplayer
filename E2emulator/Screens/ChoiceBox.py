from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.ActionMap import NumberActionMap
from Components.config import config, ConfigSubsection, ConfigText
from Components.Label import Label
from Components.ChoiceList import ChoiceEntryComponent, ChoiceList
from Components.Sources.StaticText import StaticText
import enigma

config.misc.pluginlist = ConfigSubsection()
config.misc.pluginlist.eventinfo_order = ConfigText(default="")
config.misc.pluginlist.extension_order = ConfigText(default="")

class ChoiceBox(Screen):
    def __init__(self, session, title="", list=[], keys=None, selection=0, skin_name=[], reorderConfig="", windowTitle=None):
        Screen.__init__(self, session)

        if isinstance(skin_name, str):
            skin_name = [skin_name]
        self.skinName = skin_name + ["ChoiceBox"]

        self.reorderConfig = reorderConfig
        self.list = []
        self.summarylist = []
        if keys is None:
            self.__keys = [ "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "red", "green", "yellow", "blue" ] + (len(list) - 14) * [""]
        else:
            self.__keys = keys + (len(list) - len(keys)) * [""]

        self.keymap = {}
        pos = 0

    def autoResize(self):
        pass

    def keyLeft(self):
        pass

    def keyRight(self):
        pass

    def up(self):
        pass

    def down(self):
        pass

    # runs a number shortcut
    def keyNumberGlobal(self, number):
        pass

    # runs the current selected entry
    def go(self):
        self.cancel()

    # runs a specific entry
    def goEntry(self, entry):
        self.close(entry)

    # lookups a key in the keymap, then runs it
    def goKey(self, key):
        pass

    # runs a color shortcut
    def keyRed(self):
        pass

    def keyGreen(self):
        pass

    def keyYellow(self):
        pass

    def keyBlue(self):
        pass

    def updateSummary(self, curpos=0):
        pass

    def cancel(self):
        self.close(None)

    def setDefaultChoiceList(self):
        self.cancel()

    def setDefaultChoiceListCallback(self, answer):
        if answer:
            self.cancel()

    def additionalMoveUp(self):
        pass
    def additionalMoveDown(self):
        pass
    def additionalMove(self, direction):
        pass