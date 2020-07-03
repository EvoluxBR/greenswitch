#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import pytest

from greenswitch import esl, helpers


@pytest.mark.usefixtures("outbound_session")
@pytest.mark.usefixtures("linger_disconnect_event")
@pytest.mark.usefixtures("disconnect_event")
class TestOutboundSession(unittest.TestCase):
    def test_outbound_session_disconnected(self):
        self.outbound_session.connect()
        self.assertTrue(self.outbound_session._outbound_connected)

        self.outbound_session.on_disconnect(self.disconnect_event)
        self.assertFalse(self.outbound_session._outbound_connected)

    def test_raise_on_linger_disconnect_function(self):
        self.outbound_session.connect()
        self.outbound_session.handle_event(self.linger_disconnect_event)

        with self.assertRaises(esl.OutboundSessionHasGoneAway):
            self.outbound_session.raise_if_disconnected()
