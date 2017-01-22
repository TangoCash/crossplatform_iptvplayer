# -*- coding: utf-8 -*-
#
# placeholder dla obslugi captcha z lua.
# plik oryginalny znajdujes sie pod ta samoa nazwa w katalogu components

from Screens.Screen import Screen

class UnCaptchaReCaptchaWidget(Screen):
    
    def __init__(self, session, imgFilePath, message, title, additionalParams={}):
        printDBG("UnCaptchaReCaptchaWidget.__init__ --------------------------")
        
    def __del__(self):
        printDBG("PlayerSelectorWidget.__del__ --------------------------")    
        
    def onStart(self):
        pass
                
    def keyOK(self):
        return
