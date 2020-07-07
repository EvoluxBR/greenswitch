#!/usr/bin/env python
# -*- coding: utf-8 -*-

import mock
import pytest
import textwrap

from greenswitch import esl
from tests import FakeOutboundSession


@pytest.fixture(scope="function")
def outbound_session(request):
    sock_mock = mock.MagicMock()
    client_address = mock.MagicMock()
    outbound_session = FakeOutboundSession(client_address, sock_mock)
    request.cls.outbound_session = outbound_session


@pytest.fixture(scope="function")
def disconnect_event(request):
    event_plain = """
        Content-Type: text/disconnect-notice
        Controlled-Session-UUID: e4c3f7e0-bcc1-11ea-a87f-a5a0acaa832c
        Content-Disposition: disconnect
        Content-Length: 67


        Disconnected, goodbye.
        See you at ClueCon! http://www.cluecon.com/
    """
    request.cls.disconnect_event = _create_esl_event(event_plain)


def _create_esl_event(event_plain):
    return esl.ESLEvent(textwrap.dedent(event_plain) + "\n\n")
