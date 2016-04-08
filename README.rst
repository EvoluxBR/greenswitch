GreenSWITCH: FreeSWITCH Event Socket Protocol
=============================================

.. image:: https://travis-ci.org/EvoluxBR/greenswitch.svg?branch=master
    :target: https://travis-ci.org/EvoluxBR/greenswitch

.. image:: https://img.shields.io/pypi/v/greenswitch.svg
    :target: https://pypi.python.org/pypi/greenswitch

.. image:: https://img.shields.io/pypi/dm/greenswitch.svg
    :target: https://pypi.python.org/pypi/greenswitch

Battle proven FreeSWITCH Event Socket Protocol client implementation with Gevent.

This is an implementation of FreeSWITCH Event Socket Protocol using Gevent
Greenlets. It is already in production and processing hundreds of calls per day.

.. code-block:: python

    >>> import greenswitch
    >>> fs = greenswitch.InboundESL(host='127.0.0.1', port=8021, password='ClueCon')
    >>> fs.connect()
    >>> r = fs.send('api list_users')
    >>> print r.data


Currently only Inbound Socket is implemented, support for outbound socket should
be done soon.
