#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import print_function

import logging
import gevent
import greenswitch


def on_sofia_register_failure(event):
    message = 'Failed register attempt from {network-ip} to user {to-user} profile {profile-name}'
    print(message.format(**event.headers))

fs = greenswitch.InboundESL(host='192.168.50.4', port=8021, password='ClueCon')
fs.connect()
fs.register_handle('sofia::register_failure', on_sofia_register_failure)
fs.send('EVENTS PLAIN ALL')

print('Connected to FreeSWITCH!')
while True:
    try:
        gevent.sleep(1)
    except KeyboardInterrupt:
        fs.stop()
        break
print('ESL Disconnected.')
