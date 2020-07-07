#!/usr/bin/env python
# -*- coding: utf-8 -*-

import mock
import unittest
import pytest

from greenswitch import esl


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


@pytest.mark.usefixtures("outbound_session")
@pytest.mark.usefixtures("disconnect_event")
class TestWhileConnectedMethod(unittest.TestCase):
    def setUp(self):
        self.outbound_session.connect()
        self.execute_slow_task = mock.MagicMock()

    def simulate_caller_hangup(self):
        self.outbound_session.on_disconnect(self.disconnect_event)

    def test_context_manager(self):
        with self.assertRaises(esl.OutboundSessionHasGoneAway):
            with self.outbound_session.while_connected():
                self.simulate_caller_hangup()
                self.execute_slow_task()

        self.execute_slow_task.assert_called()

    def test_decorator(self):
        @self.outbound_session.while_connected()
        def myflow():
            self.simulate_caller_hangup()
            self.execute_slow_task()

        with self.assertRaises(esl.OutboundSessionHasGoneAway):
            myflow()

        self.execute_slow_task.assert_called()

    def test_skip_code_execution_if_the_outbound_session_is_disconnected(self):
        self.simulate_caller_hangup()

        with self.assertRaises(esl.OutboundSessionHasGoneAway):
            with self.outbound_session.while_connected():
                self.execute_slow_task()

        self.execute_slow_task.assert_not_called()

    def test_raise_value_error_while_the_call_is_active(self):
        with self.assertRaises(ValueError):
            with self.outbound_session.while_connected():
                raise ValueError("http exception")
