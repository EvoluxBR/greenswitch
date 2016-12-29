#!/usr/bin/env python
# -*- coding: utf-8 -*-
import socket
import threading
import time


class FakeESLServer(object):
    def __init__(self, address, port, password):
        self._address = address
        self._port = port
        self._password = password
        self._client_socket = None
        self._running = False
        self.commands = {}
        self.setup_commands()

    def setup_commands(self):
        self.commands['api khomp show links concise'] = ('B00L00:kes{SignalLost},sync\n' +
                                                         'B01L00:kesOk,sync\n' +
                                                         'B01L01:[ksigInactive]\n')

    def start_server(self):
        self.server = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self._address, self._port))
        self.server.listen(10)
        self._running = True
        self._read_thread = threading.Thread(target=self.protocol_read)
        self._read_thread.setDaemon(True)
        self._read_thread.start()

    def command_reply(self, data):
        self._client_socket.send('Content-Type: command/reply\n'.encode('utf-8'))
        self._client_socket.send(('Reply-Text: %s\n\n' % data).encode('utf-8'))

    def protocol_send(self, lines):
        for line in lines:
            self._client_socket.send((line + '\n').encode('utf-8'))
        self._client_socket.send('\n'.encode('utf-8'))

    def api_response(self, data):
        data_length = len(data)
        self._client_socket.send('Content-Type: api/response\n'.encode('utf-8'))
        self._client_socket.send(('Content-Length: %d\n\n' % data_length).encode('utf-8'))
        self._client_socket.send(data.encode('utf-8'))

    def handle_request(self, request):
        if request.startswith('auth'):
            received_password = request.split()[-1].strip()
            if received_password == self._password:
                self.command_reply('+OK accepted')
            else:
                self.command_reply('-ERR invalid')
                self.disconnect()
        elif request == 'exit':
            self.command_reply('+OK bye')
            self.disconnect()
            self.stop()
        elif request in self.commands:
            data = self.commands.get(request)
            if request.startswith('api'):
                self.api_response(data)
            else:
                self.command_reply(data)
        else:
            if request.startswith('api'):
                self.api_response('-ERR %s Command not found\n' % request.replace('api', '').split()[0])
            else:
                self.command_reply('-ERR command not found')

    def protocol_read(self):
        self._client_socket, address = self.server.accept()
        self.protocol_send(['Content-Type: auth/request'])
        while self._running:
            buf = ''
            while self._running:
                try:
                    read = self._client_socket.recv(1)
                except Exception:
                    self._running = False
                    self.server.close()
                    break
                buf += read.decode('utf-8')
                if buf[-2:] == '\n\n' or buf[-4:] == '\r\n\r\n':
                    request = buf
                    break
            request = buf.strip()
            if not request and not self._running:
                break
            self.handle_request(request)

    def fake_event_plain(self, data):
        self.protocol_send(['Content-Type: text/event-plain',
                            'Content-Length: %s' % len(data)])
        self._client_socket.send(data)

    def fake_raw_event_plain(self, data):
        self._client_socket.send(data)

    def disconnect(self):
        self.protocol_send(['Content-Type: text/disconnect-notice',
                            'Content-Length: 67'])
        self._client_socket.send('Disconnected, goodbye.\n'.encode('utf-8'))
        self._client_socket.send('See you at ClueCon! http://www.cluecon.com/\n'.encode('utf-8'))
        self._running = False
        self._client_socket.close()

    def stop(self):
        self._client_socket.close()
        self.server.close()
        if self._running:
            self._running = False
            self._read_thread.join(5)


def main():
    server = FakeESLServer('0.0.0.0', 8021, 'ClueCon')
    server.start_server()
    while server._running:
        time.sleep(1)
    server.stop()


if __name__ == '__main__':
    main()
