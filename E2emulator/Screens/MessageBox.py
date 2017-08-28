#TBC - show msgbox using neutrino

class MessageBox():
	TYPE_YESNO = 0
	TYPE_INFO = 1
	TYPE_WARNING = 2
	TYPE_ERROR = 3
	TYPE_MESSAGE = 4

	def __init__(self, session, text, type=TYPE_YESNO, timeout=-1, close_on_any_key=False, default=True, enable_input=True, msgBoxID=None, picon=None, simple=False, list=[], timeout_default=None):
		return	  
		self.type = type
		self.msgBoxID = msgBoxID
	      
		self.text = text
		self.close_on_any_key = close_on_any_key
		self.timeout_default = timeout_default

		self.timerRunning = False
		self.initTimeout(timeout)

		if type == self.TYPE_YESNO:
			if list:
				self.list = list
			elif default == True:
				self.list = [ (_("yes"), True), (_("no"), False) ]
			else:
				self.list = [ (_("no"), False), (_("yes"), True) ]
		else:
			self.list = []

	def initTimeout(self, timeout):
		if timeout > 0:
			import time
			time.sleep(timeout)

	def __onShown(self):
		pass

	def startTimer(self):
		pass

	def stopTimer(self):
		pass

	def timerTick(self):
		pass

	def timeoutCallback(self):
		pass

	def cancel(self):
		pass

	def ok(self):
		pass

	def alwaysOK(self):
		pass

	def up(self):
		pass

	def down(self):
		pass

	def left(self):
		pass

	def right(self):
		pass

	def move(self, direction):
		pass

	def __repr__(self):
		pass
