#-*- coding: utf-8 -*-
#
# Djeman
#

import re

class AADecoder(object):

    def __init__(self, aa_encoded_data):
        self.encoded_str = aa_encoded_data

    def is_aaencoded(self):
        if self.encoded_str.find("ﾟωﾟﾉ= /｀ｍ´）ﾉ ~┻━┻   //*´∇｀*/ ['_']; o=(ﾟｰﾟ)  =_=3; c=(ﾟΘﾟ) =(ﾟｰﾟ)-(ﾟｰﾟ); ") == -1:
            return False

        if self.encoded_str.find("(ﾟДﾟ)[ﾟoﾟ]) (ﾟΘﾟ)) ('_');") == -1:
            return False

        return True;

    def clean(self):
        return re.sub('^\s+|\s+$', '', self.encoded_str)

    def base_repr(self, number, base=2, padding=0):
        digits = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        if base > len(digits):
            base = len(digits)
        
        num = abs(number)
        res = []
        while num:
            res.append(digits[num % base])
            num //= base
        if padding:
            res.append('0' * padding)
        if number < 0:
            res.append('-')
        return ''.join(reversed(res or '0'))

    def decode(self):
        self.encoded_str = self.clean()

        # get data
        pattern = (r"\(ﾟДﾟ\)\[ﾟoﾟ\]\+ (.+?)\(ﾟДﾟ\)\[ﾟoﾟ\]\)")
        result = re.search(pattern, self.encoded_str, re.DOTALL)
        if result == None:
            print "AADecoder: data not found"
            return False

        data = result.group(1)

        # hex decode string
        b = ["(c^_^o)","(ﾟΘﾟ)","((o^_^o) - (ﾟΘﾟ) +(c^_^o))","(o^_^o)","(ﾟｰﾟ)","((ﾟｰﾟ) + (ﾟΘﾟ))","((o^_^o) +(o^_^o) +(c^_^o))","((ﾟｰﾟ) + (o^_^o))","((ﾟｰﾟ) + (ﾟｰﾟ))",
            "((ﾟｰﾟ) + (ﾟｰﾟ) + (ﾟΘﾟ))","(ﾟДﾟ) .ﾟωﾟﾉ","(ﾟДﾟ) .ﾟΘﾟﾉ","(ﾟДﾟ) ['c']","(ﾟДﾟ) .ﾟｰﾟﾉ","(ﾟДﾟ) .ﾟДﾟﾉ","(ﾟДﾟ) [ﾟΘﾟ]"]
        
        begin_char = "(ﾟДﾟ)[ﾟεﾟ]+"
        alt_char = "(oﾟｰﾟo)+ "
        end_char = "+ "

        out = ''
        while data != '':
            # Check new char
            if data.find(begin_char) != 0:
                print "AADecoder: data not found"
                return False

            data = data[len(begin_char):]
            
            # Find encoded char
            enc_char = ""
            if data.find(begin_char) == -1:
                enc_char = data
                data = ""
            else:
                enc_char = data[:data.find(begin_char)]
                data = data[len(enc_char):]

            radix = 8
            # Detect radix 16 for utf8 char
            if enc_char.find(alt_char) == 0:
                enc_char = enc_char[len(alt_char):]
                radix = 16

            str_char = ""
            while enc_char != '':
                for i in range(len(b)):
                    if enc_char.find(b[i]) == 0:
                        str_char += self.base_repr(i, radix)
                        enc_char = enc_char[len(b[i]):]
                        break
                    
                    if i == (len(b) - 1):
                        print "no match in b array: " + enc_char
                        return False
                
                enc_char = enc_char[len(end_char):]

            if str_char == "":
                print "no match : " + data
                return False
            
            out += chr(int(str_char, radix))

        if out == "":
            print "no match : " + data
            return False

        return out