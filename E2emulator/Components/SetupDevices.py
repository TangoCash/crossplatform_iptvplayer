from config import config, ConfigSelection, ConfigSubsection, ConfigOnOff, ConfigText
#from Components.Timezones import timezones
from Components.Language import language
#from Components.Keyboard import keyboard
import os

def InitSetupDevices():

	'''	def timezoneNotifier(configElement):
		timezones.activateTimezone(configElement.index)

	config.timezone = ConfigSubsection();
	config.timezone.val = ConfigSelection(default = timezones.getDefaultTimezone(), choices = timezones.getTimezoneList())
	config.timezone.val.addNotifier(timezoneNotifier)

	def keyboardNotifier(configElement):
		keyboard.activateKeyboardMap(configElement.index)

	config.keyboard = ConfigSubsection();
	config.keyboard.keymap = ConfigSelection(default = keyboard.getDefaultKeyboardMap(), choices = keyboard.getKeyboardMaplist())
	config.keyboard.keymap.addNotifier(keyboardNotifier)
'''
	def languageNotifier(configElement):
		language.activateLanguage(configElement.value)

	config.osd = ConfigSubsection()
	
	if os.path.exists('/var/tuxbox/config/neutrino.conf'):
		with open('/var/tuxbox/config/neutrino.conf', 'r') as f:
			for line in f.readlines():
				if line.startswith('language='):
					lang = line.split("=")[1].strip()
					if lang == 'polski':
						config.osd.language = ConfigText(default = "pl_PL");
					elif lang == 'deutsch':
						config.osd.language = ConfigText(default = "de_DE");
					else:
						config.osd.language = ConfigText(default = "en_EN");
						
	config.osd.language.addNotifier(languageNotifier)

	config.parental = ConfigSubsection();
	config.parental.lock = ConfigOnOff(default = False)
	config.parental.setuplock = ConfigOnOff(default = False)

	config.expert = ConfigSubsection();
	config.expert.satpos = ConfigOnOff(default = True)
	config.expert.fastzap = ConfigOnOff(default = True)
	config.expert.skipconfirm = ConfigOnOff(default = False)
	config.expert.hideerrors = ConfigOnOff(default = False)
	config.expert.autoinfo = ConfigOnOff(default = True)
