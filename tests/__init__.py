#!/usr/bin/env python
# -*- coding: utf-8 -*-


from gevent import monkey; monkey.patch_all()

import gevent
import os
import unittest

from . import fakeeslserver
from greenswitch import esl


class TestInboundESLBase(unittest.TestCase):

    esl_class = esl.InboundESL

    def setUp(self):
        super(TestInboundESLBase, self).setUp()
        self.switch_esl = fakeeslserver.FakeESLServer('0.0.0.0', 8021, 'ClueCon')
        self.switch_esl.start_server()
        self.esl = self.esl_class('127.0.0.1', 8021, 'ClueCon')
        self.esl.connect()

    def tearDown(self):
        super(TestInboundESLBase, self).tearDown()
        self.esl.stop()
        self.switch_esl.stop()

    def send_fake_event_plain(self, data):
        self.switch_esl.fake_event_plain(data.encode('utf-8'))
        gevent.sleep(0.1)

    def send_fake_raw_event_plain(self, data):
        self.switch_esl.fake_raw_event_plain(data.encode('utf-8'))
        gevent.sleep(0.1)


    def send_batch_fake_event_plain(self, events):
        for event in events:
            self.send_fake_event_plain(event)
        gevent.sleep(0.1)


class FakeOutboundSession(esl.OutboundSession):
    def start_event_handlers(self):
        pass

    def send(self, command):
        return esl.ESLEvent('')

if __name__ == '__main__':
    unittest.main()
