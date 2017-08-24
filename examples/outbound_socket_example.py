#!/usr/bin/env python

import gevent
import greenswitch


class MyApplication(object):
    def __init__(self, session):
        self.session = session

    def run(self):
        """
        Main function that is called when a call comes in.
        """
        self.session.myevents()
        self.session.linger()
        self.session.answer()
        gevent.sleep(1)
        # Now block until the end of the file. pass block=False to
        # return immediately.
        self.session.playback('ivr/ivr-welcome')
        # blocks until the caller presses a digit
        digit = self.session.play_and_get_digits('1', '1', '3', '5000', '#',
                                                 'conference/conf-pin.wav',
                                                 'invalid.wav',
                                                 'test', '\d', '1000', "''",
                                                 block=True, response_timeout=30)
        print("User typed: %s" % digit)
        # Start music on hold in background and let's do another thing
        # block=False makes the playback function return immediately.
        self.session.playback('local_stream://default', block=False)
        # Now we can do a long task, for example, processing a payment
        gevent.sleep(5)
        # Stopping the music on hold
        self.session.uuid_break()
        self.session.hangup()


server = greenswitch.OutboundESLServer(bind_address='0.0.0.0',
                                       bind_port=5000,
                                       application=MyApplication)
server.listen()