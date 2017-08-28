from enigma import gRGB

colorNames = {}
# Predefined fonts, typically used in built-in screens and for components like
# the movie list and so.
fonts = {
	"Body": ("Regular", 18, 22, 16),
	"ChoiceList": ("Regular", 20, 24, 18),
}

parameters = {}

def parseColor(s):
	if s[0] != '#':
		try:
			return colorNames[s]
		except Exception:
			print SkinError("color '%s' must be #aarrggbb or valid named color" % s)
	return gRGB(int(s[1:], 0x10))
