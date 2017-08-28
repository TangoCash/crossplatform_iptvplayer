from Screen import Screen
from Rc import Rc

class HelpMenu(Screen, Rc):
    def __init__(self, session, list):
        pass

    def SelectionChanged(self):
        pass

class HelpableScreen:
    def __init__(self):
        pass

    def showHelp(self):
        pass

    def callHelpAction(self, *args):
        pass
