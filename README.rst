GreenSWITCH: FreeSWITCH Event Socket Protocol
=============================================

.. image:: https://github.com/EvoluxBR/greenswitch/actions/workflows/tests.yml/badge.svg
    :target: https://github.com/EvoluxBR/greenswitch/actions

.. image:: https://img.shields.io/pypi/v/greenswitch.svg
    :target: https://pypi.python.org/pypi/greenswitch

.. image:: https://img.shields.io/pypi/dm/greenswitch.svg
    :target: https://pypi.python.org/pypi/greenswitch

Battle proven FreeSWITCH Event Socket Protocol client implementation with Gevent.

This is an implementation of FreeSWITCH Event Socket Protocol using Gevent
Greenlets. It is already in production and processing hundreds of calls per day.

Full Python3 support!

Inbound Socket Mode
===================

.. code-block:: python

    >>> import greenswitch
    >>> fs = greenswitch.InboundESL(host='127.0.0.1', port=8021, password='ClueCon')
    >>> fs.connect()
    >>> r = fs.send('api list_users')
    >>> print r.data


Outbound Socket Mode
====================

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

Example of Outbound Socket Mode:

.. code-block:: python

    '''
    Add a extension on your dialplan to bound the outbound socket on FS channel
    as example below

    <extension name="out socket">
        <condition>
            <action application="socket" data="<outbound socket server host>:<outbound socket server port> async full"/>
        </condition>
    </extension>

    Or see the complete doc on https://freeswitch.org/confluence/display/FREESWITCH/mod_event_socket
    '''
    import gevent
    import greenswitch

    import logging
    logging.basicConfig(level=logging.DEBUG)


    class MyApplication(object):
        def __init__(self, session):
            self.session = session

        def run(self):
            """
            Main function that is called when a call comes in.
            """
            try:
                self.handle_call()
            except:
                logging.exception('Exception raised when handling call')
                self.session.stop()

        def handle_call(self):
            # We want to receive events related to this call
            # They are also needed to know when an application is done running
            # for example playback
            self.session.myevents()
            print("myevents")
            # Send me all the events related to this call even if the call is already
            # hangup
            self.session.linger()
            print("linger")
            self.session.answer()
            print("answer")
            gevent.sleep(1)
            print("sleep")
            # Now block until the end of the file. pass block=False to
            # return immediately.
            self.session.playback('ivr/ivr-welcome')
            print("welcome")
            # blocks until the caller presses a digit, see response_timeout and take
            # the audio length in consideration when choosing this number
            digit = self.session.play_and_get_digits('1', '1', '3', '5000', '#',
                                                     'conference/conf-pin.wav',
                                                     'invalid.wav',
                                                     'test', '\d', '1000', "''",
                                                     block=True, response_timeout=5)
            print("User typed: %s" % digit)
            # Start music on hold in background without blocking code execution
            # block=False makes the playback function return immediately.
            self.session.playback('local_stream://default', block=False)
            print("moh")
            # Now we can do a long task, for example, processing a payment,
            # consuming an APIs or even some database query to find our customer :)
            gevent.sleep(5)
            print("sleep 5")
            # We finished processing, stop the music on hold and do whatever you want
            # Note uuid_break is a general API and requires full permission
            self.session.uuid_break()
            print("break")
            # Bye caller
            self.session.hangup()
            print("hangup")
            # Close the socket so freeswitch can leave us alone
            self.session.stop()

        server = greenswitch.OutboundESLServer(bind_address='0.0.0.0',
                                       bind_port=5000,
                                       application=MyApplication,
                                       max_connections=5)
        server.listen()


Enjoy!

Feedbacks always welcome.
