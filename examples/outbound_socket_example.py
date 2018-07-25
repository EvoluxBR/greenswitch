#!/usr/bin/env python

import gevent
import greenswitch

import logging
logging.basicConfig(level=logging.DEBUG)


"""
Add a extension on your dialplan to bound the outbound socket on FS channel
as example below

<extension name="out socket">
    <condition>
        <action application="socket" data="<outbound socket server host>:<outbound socket server port> sync full"/>
    </condition>
</extension>

Or see the complete doc on https://freeswitch.org/confluence/display/FREESWITCH/mod_event_socket
"""

class MyApplication(object):
    def __init__(self, session):
        self.session = session

    def run(self):
        # TODO(italo): Move the safe_run logic to inside the lib,
        # this is not the user task.
        try:
            self.safe_run()
        except:
            print('ERRORRR')
            logging.exception('Exception raised when handling call')
            self.session.stop()

    def safe_run(self):
        """
        Main function that is called when a call comes in.
        """
        self.session.connect()
        self.session.myevents()
        print("myevents")
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
        # blocks until the caller presses a digit
        digit = self.session.play_and_get_digits('1', '1', '3', '5000', '#',
                                                 'conference/conf-pin.wav',
                                                 'invalid.wav',
                                                 'test', '\d', '1000', "''",
                                                 block=True, response_timeout=5)
        print("User typed: %s" % digit)
        # Start music on hold in background and let's do another thing
        # block=False makes the playback function return immediately.
        self.session.playback('local_stream://default', block=False)
        print("moh")
        # Now we can do a long task, for example, processing a payment
        gevent.sleep(5)
        print("sleep 5")
        # Stopping the music on hold
        self.session.uuid_break()
        print("break")
        # self.session.hangup()
        # print("hangup")


server = greenswitch.OutboundESLServer(bind_address='0.0.0.0',
                                       bind_port=5000,
                                       application=MyApplication,
                                       max_connections=5)
server.listen()
