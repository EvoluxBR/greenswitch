# Gevent imports
import gevent
import sys
from gevent.queue import Queue
import gevent.socket as socket
from gevent.event import Event
import logging
import pprint
from six.moves.urllib.parse import unquote


class NotConnectedError(Exception):
    pass


class ESLEvent(object):
    def __init__(self, data):
        self.parse_data(data)

    def parse_data(self, data):
        headers = {}
        data = unquote(data)
        data = data.strip().splitlines()
        last_key = None
        value = ''
        for line in data:
            if ': ' in line:
                key, value = line.split(': ', 1)
                last_key = key
            else:
                key = last_key
                value += '\n' + line
            headers[key.strip()] = value.strip()
        self.headers = headers


class InboundESL(object):
    def __init__(self, host, port, password):
        self.host = host
        self.port = port
        self.password = password
        self.timeout = 5
        self._run = True
        self._EOL = '\n'
        self._commands_sent = []
        self._auth_request_event = Event()
        self._receive_events_greenlet = None
        self._process_events_greenlet = None
        self.event_handlers = {}
        self.connected = False

        self._esl_event_queue = Queue()
        self._process_esl_event_queue = True

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect((self.host, self.port))
        self.connected = True
        self.sock.settimeout(None)
        self.sock_file = self.sock.makefile()
        self._receive_events_greenlet = gevent.spawn(self.receive_events)
        self._process_events_greenlet = gevent.spawn(self.process_events)
        self._auth_request_event.wait()
        self.authenticate()

    def receive_events(self):
        buf = ''
        while self._run:
            try:
                data = self.sock_file.readline()
            except Exception:
                self._run = False
                self.connected = False
                self.sock.close()
                # logging.exception("Error reading from socket.")
                break
            if not data:
                if self.connected:
                    logging.error("Error receiving data, is FreeSWITCH running?")
                    self.connected = False
                break
            # Empty line
            if data == self._EOL:
                event = ESLEvent(buf)
                buf = ''
                self.handle_event(event)
                continue
            buf += data

    @staticmethod
    def _read_socket(sock, length):
        """Receive data from socket until the length is reached."""
        data = sock.read(length)
        data_length = len(data)
        while data_length < length:
            logging.warn(
                'Socket should read %s bytes, but actually read %s bytes. '
                'Consider increasing "net.core.rmem_default".' %
                (length, data_length)
            )
            # FIXME(italo): if not data raise error
            data += sock.read(length - data_length)
            data_length = len(data)
        return data

    def handle_event(self, event):
        if event.headers['Content-Type'] == 'auth/request':
            self._auth_request_event.set()
        elif event.headers['Content-Type'] == 'command/reply':
            async_response = self._commands_sent.pop(0)
            event.data = event.headers['Reply-Text']
            async_response.set(event)
        elif event.headers['Content-Type'] == 'api/response':
            length = int(event.headers['Content-Length'])
            data = self._read_socket(self.sock_file, length)
            event.data = data
            async_response = self._commands_sent.pop(0)
            async_response.set(event)
        elif event.headers['Content-Type'] == 'text/disconnect-notice':
            self.connected = False
        else:
            length = int(event.headers['Content-Length'])
            data = self._read_socket(self.sock_file, length)
            if event.headers.get('Content-Type') == 'log/data':
                event.data = data
            else:
                event.parse_data(data)
            self._esl_event_queue.put(event)

    def _safe_exec_handler(self, handler, event):
        try:
            handler(event)
        except:
            logging.exception('ESL %s raised exception.' % handler.__name__)
            logging.error(pprint.pformat(event.headers))

    def process_events(self):
        logging.debug('Event Processor Running')
        while self._run:
            if not self._process_esl_event_queue:
                gevent.sleep(1)
                continue

            try:
                event = self._esl_event_queue.get(timeout=1)
            except gevent.queue.Empty:
                continue

            if event.headers.get('Event-Name') == 'CUSTOM':
                handlers = self.event_handlers.get(event.headers.get('Event-Subclass'))
            else:
                handlers = self.event_handlers.get(event.headers.get('Event-Name'))

            if not handlers and event.headers.get('Content-Type') == 'log/data':
                handlers = self.event_handlers.get('log')

            if not handlers:
                continue

            if hasattr(self, 'before_handle'):
                self._safe_exec_handler(self.before_handle, event)

            for handle in handlers:
                self._safe_exec_handler(handle, event)

            if hasattr(self, 'after_handle'):
                self._safe_exec_handler(self.after_handle, event)

    def send(self, data):
        if not self.connected:
            raise NotConnectedError()
        async_response = gevent.event.AsyncResult()
        self._commands_sent.append(async_response)
        raw_msg = (data + self._EOL*2).encode('utf-8')
        self.sock.send(raw_msg)
        response = async_response.get()
        return response

    def authenticate(self):
        response = self.send('auth %s' % self.password)
        if response.headers['Reply-Text'] != '+OK accepted':
            raise ValueError('Invalid password.')

    def register_handle(self, name, handler):
        if name not in self.event_handlers:
            self.event_handlers[name] = []
        if handler in self.event_handlers[name]:
            return
        self.event_handlers[name].append(handler)

    def unregister_handle(self, name, handler):
        if name not in self.event_handlers:
            raise ValueError('No handlers found for event: %s' % name)
        self.event_handlers[name].remove(handler)
        if not self.event_handlers[name]:
            del self.event_handlers[name]

    def stop(self):
        if self.connected:
            self.send('exit')
        self._run = False
        logging.info("Waiting for receive greenlet exit")
        self._receive_events_greenlet.join()
        logging.info("Waiting for event processing greenlet exit")
        self._process_events_greenlet.join()
        if self.connected:
            self.sock.close()
            self.sock_file.close()
