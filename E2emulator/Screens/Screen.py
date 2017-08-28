
class Screen():

	False, SUSPEND_STOPS, SUSPEND_PAUSES = range(3)
	ALLOW_SUSPEND = False

	global_screen = None

	def __init__(self, session = None, parent = None):
		pass

	def saveKeyboardMode(self):
		pass

	def setKeyboardModeAscii(self):
		pass

	def setKeyboardModeNone(self):
		pass

	def restoreKeyboardMode(self):
		pass

	def execBegin(self):
		pass

	def execEnd(self):
		pass

	def doClose(self):
		pass

	def close(self, *retval):
		pass

	def setFocus(self, o):
		pass

	def show(self):
		pass

	def hide(self):
		pass

	def __repr__(self):
		pass

	def getRelatedScreen(self, name):
		pass
