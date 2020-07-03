#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import mock
import pytest

from greenswitch import esl, helpers


@pytest.mark.usefixtures("outbound_session")
@pytest.mark.usefixtures("linger_disconnect_event")
class TestWhileConnected(unittest.TestCase):
    def setUp(self):
        self.outbound_session.connect()
        self.execute_slow_task = mock.MagicMock()

    def simulate_caller_hangup(self):
        self.outbound_session.handle_event(self.linger_disconnect_event)

    def test_context_manager(self):
        with self.assertRaises(esl.OutboundSessionHasGoneAway):
            with helpers.while_connected(self.outbound_session):
                self.simulate_caller_hangup()
                self.execute_slow_task()

        self.execute_slow_task.assert_called()

    def test_decorator(self):
        @helpers.while_connected(self.outbound_session)
        def myflow():
            self.simulate_caller_hangup()
            self.execute_slow_task()

        with self.assertRaises(esl.OutboundSessionHasGoneAway):
            myflow()

        self.execute_slow_task.assert_called()

    def test_skip_code_execution_if_the_outbound_session_is_disconnected(self):
        self.simulate_caller_hangup()

        with self.assertRaises(esl.OutboundSessionHasGoneAway):
            with helpers.while_connected(self.outbound_session):
                self.execute_slow_task()

        self.execute_slow_task.assert_not_called()

    def test_raise_value_error_while_the_call_is_active(self):
        with self.assertRaises(ValueError):
            with helpers.while_connected(self.outbound_session):
                raise ValueError("http exception")
