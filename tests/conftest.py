#!/usr/bin/env python
# -*- coding: utf-8 -*-

import mock
import pytest

from tests import FakeOutboundSession


@pytest.fixture(scope='class')
def outbound_session(request):
    sock_mock = mock.MagicMock()
    client_address = mock.MagicMock()
    outbound_session = FakeOutboundSession(client_address, sock_mock)
    request.cls.outbound_session = outbound_session