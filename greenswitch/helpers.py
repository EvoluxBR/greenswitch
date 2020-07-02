#!/usr/bin/env python
# -*- coding: utf-8 -*-

import functools


class while_connected(object):
    """while_connected is a helper class that will verify if the session is
    connected in the __enter__ and __exit__ steps, if not connected will
    raise the greenswitch.esl.OutboundSessionHasGoneAway exception.

    This class can be used as a context manager or decorator.

    Example:
    >>> with while_connected(outbound_session):
    >>>    do_something()
    >>>
    >>> @while_connected(outbound_session)
    >>> def do_something():
    >>>     ...
    """

    def __init__(self, outbound_session):
        self.outbound_session = outbound_session

    def __enter__(self):
        self.outbound_session.raise_if_disconnected()
        return self

    def __exit__(self, exit_type, exit_value, exit_traceback):
        self.outbound_session.raise_if_disconnected()

    def __call__(self, func):
        @functools.wraps(func)
        def decorator(*args, **kwargs):
            with self:
                return func(*args, **kwargs)

        return decorator
