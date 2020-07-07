#!/usr/bin/env python
# -*- coding: utf-8 -*-

import mock
import unittest
import pytest

from greenswitch import esl, helpers


@pytest.mark.usefixtures("outbound_session")
@pytest.mark.usefixtures("disconnect_event")
class TestOutboundSession(unittest.TestCase):
    def test_outbound_connected_is_updated_during_on_disconnected_event(self):
        self.outbound_session.connect()
        self.assertTrue(self.outbound_session._outbound_connected)

        self.outbound_session.on_disconnect(self.disconnect_event)
        self.assertFalse(self.outbound_session._outbound_connected)

    def test_outbound_connected_is_updated_during_on_hangup_event(self):
        self.outbound_session.connect()
        self.outbound_session.on_hangup(mock.MagicMock())

        with self.assertRaises(esl.OutboundSessionHasGoneAway):
            self.outbound_session.raise_if_disconnected()
