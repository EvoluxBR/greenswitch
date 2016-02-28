#!/usr/bin/env python
# -*- coding: utf-8 -*-


from gevent import monkey; monkey.patch_all()

import gevent
import os
import unittest

import fakeeslserver
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
        self.esl.sock.close()
        self.switch_esl.stop()

    def send_fake_event_plain(self, data):
        self.switch_esl.fake_event_plain(data)
        gevent.sleep(0.1)

    def send_batch_fake_event_plain(self, events):
        for event in events:
            self.send_fake_event_plain(event)
        gevent.sleep(0.1)

if __name__ == '__main__':
    unittest.main()
