# -*- coding: utf-8 -*-

"""
GreenSWITCH: FreeSWITCH Event Socket Protocol
---------------------------------------------

Complete documentation at https://github.com/italorossi/greenswitch

"""

import sys
# Avoiding threading KeyError when exiting
if 'threading' in sys.modules:
    del sys.modules['threading']

from gevent import monkey; monkey.patch_all()

from .esl import InboundESL
