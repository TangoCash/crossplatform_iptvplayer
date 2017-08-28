import time

recorded_events = [ ]

def event(self, name, args, kwargs):
	global recorded_events
	print "*EVENT*", time.time(), self, name, args, kwargs
	recorded_events.append((time.time(), self, name, args, kwargs))

def eventfnc(f):
	name = f.__name__
	def wrapper(self, *args, **kwargs):
		event(self, name, args, kwargs)
		return f(self, *args, **kwargs)
	return wrapper

def get_events():
	global recorded_events
	r = recorded_events
	recorded_events = [ ]
	return r
