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

Inbound Socket Mode

.. code-block:: python

    >>> import greenswitch
    >>> fs = greenswitch.InboundESL(host='127.0.0.1', port=8021, password='ClueCon')
    >>> fs.connect()
    >>> r = fs.send('api list_users')
    >>> print r.data


Currently only Inbound Socket is implemented, support for outbound socket should
be done soon.


Outbound Socket Mode

Outbound is implemented with sync and async support. The main idea is to create
an Application that will be called passing an OutboundSession as argument.
This OutboundSession represents a call that is handled by the ESL connection.
Basic functions are implemented already:

 - playback
 - play_and_get_digits
 - hangup
 - park
 - uuid_kill
 - answer
 - sleep

With current api, it's easy to mix sync and async actions, for example:
play_and_get_digits method will return the pressed DTMF digits in a block mode,
that means as soon as you call that method in your Python code the execution
flow will block and wait for the application to end only returning to the next
line after ending the application. But after getting digits, if you need to consume
an external system, like posting this to an external API you can leave the caller
hearing MOH while the API call is being done, you can call the playback method
with block=False, playback('my_moh.wav', block=False), after your API end we need
to tell FreeSWITCH to stop playing the file and give us back the call control,
for that we can use uuid_kill method.

A very good example implementation is here https://github.com/EvoluxBR/greenswitch/blob/outboundsocket/examples/outbound_socket_example.py

Enjoy!

Feedbacks always welcome.