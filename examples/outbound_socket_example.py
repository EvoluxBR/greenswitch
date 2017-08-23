#!/usr/bin/env python

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
        # Returns immediately
        self.session.playback('local_stream://default')
        # blocks until the caller presses a digit
        digit = self.session.play_and_get_digits('1', '1', '3', '5000', '#',
                                                 'conference/conf-pin.wav',
                                                 'invalid.wav',
                                                 'test', '\d', '1000', "''",
                                                 block=True, response_timeout=30)
        print("User typed: %s" % digit)


server = greenswitch.OutboundESLServer(bind_address='0.0.0.0',
                                       bind_port=5000,
                                       application=MyApplication)
server.listen()