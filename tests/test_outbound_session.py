#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import pytest

from greenswitch import esl, helpers


@pytest.mark.usefixtures("outbound_session")
class TestOutboundSession(unittest.TestCase):
    def test_on_hangup_set_outbound_connected_to_false(self):
        self.outbound_session.connect()
        self.assertTrue(self.outbound_session._outbound_connected)

        self.outbound_session.on_hangup(None)
        self.assertFalse(self.outbound_session._outbound_connected)

    def test_raise_on_disconnect_function(self):
        self.outbound_session.connect()
        self.outbound_session.on_hangup(None)

        with self.assertRaises(esl.OutboundSessionHasGoneAway):
            self.outbound_session.raise_if_disconnected()
