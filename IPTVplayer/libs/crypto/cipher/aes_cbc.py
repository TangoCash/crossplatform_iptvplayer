# -*- coding: iso-8859-1 -*-
""" crypto.cipher.aes_cbc

    AES_CBC Encryption Algorithm

    Copyright � (c) 2002 by Paul A. Lambert
    Read LICENSE.txt for license information.

    2002-06-14
"""

from aes import AES
from cbc import CBC
from base import BlockCipher, padWithPadLen, noPadding


class AES_CBC(CBC):
    """ AES encryption in CBC feedback mode """

    def __init__(self, key=None, padding=padWithPadLen(), keySize=16):
        CBC.__init__(self, AES(key, noPadding(), keySize), padding)
        self.name = 'AES_CBC'
