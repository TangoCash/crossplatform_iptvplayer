from HTMLComponent import HTMLComponent
from GUIComponent import GUIComponent

from enigma import eListboxPythonStringContent, eListbox

class MenuList(HTMLComponent, GUIComponent):
    def __init__(self, list, enableWrapAround=True, content=eListboxPythonStringContent):
        GUIComponent.__init__(self)
        self.list = list
        self.onSelectionChanged = [ ]
        self.enableWrapAround = enableWrapAround

    def getCurrent(self):
        pass

    GUI_WIDGET = eListbox

    def postWidgetCreate(self, instance):
        pass

    def preWidgetRemove(self, instance):
        pass

    def selectionChanged(self):
        pass

    def getSelectionIndex(self):
        return 0

    def getSelectedIndex(self):
        return 0

    def setList(self, list):
        pass

    def moveToIndex(self, idx):
        pass

    def pageUp(self):
        pass

    def pageDown(self):
        pass

    def up(self):
        pass

    def down(self):
        pass

    def selectionEnabled(self, enabled):
        pass
