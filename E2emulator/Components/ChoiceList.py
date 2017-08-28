from MenuList import MenuList
from Tools.Directories import SCOPE_CURRENT_SKIN, resolveFilename
from enigma import RT_HALIGN_LEFT, eListboxPythonMultiContent, gFont
from Tools.LoadPixmap import LoadPixmap
import skin

def ChoiceEntryComponent(key = None, text = ["--"]):
    res = [ text ]
    return res

class ChoiceList(MenuList):
    def __init__(self, list, selection = 0, enableWrapAround=False):
        pass

    def postWidgetCreate(self, instance):
        pass
