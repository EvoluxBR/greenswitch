# Gevent imports
import gevent
import sys
from gevent.queue import Queue
import gevent.socket as socket
from gevent.pool import Pool as GeventPool
from gevent.event import Event
import logging
import pprint
from six.moves.urllib.parse import unquote


class NotConnectedError(Exception):
    pass


class OutboundSessionHasGoneAway(Exception):
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


class ESLProtocol(object):
    def __init__(self):
        self._run = True
        self._EOL = '\n'
        self._commands_sent = []
        self._auth_request_event = Event()
        self._receive_events_greenlet = None
        self._process_events_greenlet = None
        self.event_handlers = {}
        self._esl_event_queue = Queue()
        self._process_esl_event_queue = True
        self._lingering = False

    def start_event_handlers(self):
        self._receive_events_greenlet = gevent.spawn(self.receive_events)
        self._process_events_greenlet = gevent.spawn(self.process_events)

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
            if event.headers.get('Content-Disposition') == 'linger':
                logging.debug('Linger activated')
                self._lingering = True
            else:
                self.connected = False
            # disconnect-notice is now a propagated event both for inbound
            # and outbound socket modes.
            # This is useful for outbound mode to notify all remaining
            # waiting commands to stop blocking and send a NotConnectedError
            self._esl_event_queue.put(event)
        elif event.headers['Content-Type'] == 'text/rude-rejection':
            self.connected = False
            length = int(event.headers['Content-Length'])
            self._read_socket(self.sock_file, length)
            self._auth_request_event.set()
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

            if not handlers and '*' in self.event_handlers:
                handlers = self.event_handlers.get('*')

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


class InboundESL(ESLProtocol):
    def __init__(self, host, port, password):
        super(InboundESL, self).__init__()
        self.host = host
        self.port = port
        self.password = password
        self.timeout = 5
        self.connected = False

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect((self.host, self.port))
        self.connected = True
        self.sock.settimeout(None)
        self.sock_file = self.sock.makefile()
        self.start_event_handlers()
        self._auth_request_event.wait()
        if not self.connected:
            raise NotConnectedError('Server closed connection, check FreeSWITCH config.')
        self.authenticate()

    def authenticate(self):
        response = self.send('auth %s' % self.password)
        if response.headers['Reply-Text'] != '+OK accepted':
            raise ValueError('Invalid password.')


class OutboundSession(ESLProtocol):
    def __init__(self, client_address, sock):
        super(OutboundSession, self).__init__()
        self.sock = sock
        self.sock_file = self.sock.makefile()
        self.connected = True
        self.session_data = None
        self.start_event_handlers()
        self.connect()
        self.register_handle('*', self.on_event)
        self.register_handle('CHANNEL_HANGUP', self.on_hangup)
        self.expected_events = {}

    @property
    def uuid(self):
        return self.session_data.get('variable_uuid')

    @property
    def call_uuid(self):
        return self.session_data.get('variable_call_uuid')

    def on_hangup(self, event):
        logging.info('Caller %s has gone away.' % event.headers.get('Caller-Caller-ID-Number'))

    def on_event(self, event):
        # FIXME(italo): Decide if we really need a list of expected events
        # for each expected event. Since we're interacting with the call from
        # just one greenlet we don't have more than one item on this list.
        event_name = event.headers.get('Event-Name')
        if event_name not in self.expected_events:
            return

        for expected_event in self.expected_events[event_name]:
            event_variable, expected_value, async_response = expected_event
            expected_variable = 'variable_%s' % event_variable
            if expected_variable not in event.headers:
                return
            elif expected_value == event.headers.get(expected_variable):
                async_response.set(event)
                self.expected_events[event_name].remove(expected_event)

    def call_command(self, app_name, app_args=None):
        """Wraps app_name and app_args into FreeSWITCH Outbound protocol:
        Example:
                sendmsg
                call-command: execute
                execute-app-name: answer\n\n

        """
        # We're not allowed to send more commands.
        # lingering True means we already received a hangup from the caller
        # and any commands sent at this time to the session will fail
        if self._lingering:
            raise OutboundSessionHasGoneAway()

        command = "sendmsg\n" \
                  "call-command: execute\n" \
                  "execute-app-name: %s" % app_name
        if app_args:
            command += "\nexecute-app-arg: %s" % app_args

        return self.send(command)

    def connect(self):
        resp = self.send('connect')
        self.session_data = resp.headers

    def myevents(self):
        self.send('myevents')

    def answer(self):
        resp = self.call_command('answer')
        return resp.data

    def park(self):
        self.call_command('park')

    def linger(self):
        self.send('linger')

    def playback(self, path, block=True):
        if not block:
            self.call_command('playback', path)
            return

        async_response = gevent.event.AsyncResult()
        expected_event = "CHANNEL_EXECUTE_COMPLETE"
        expected_variable = "current_application"
        expected_variable_value = "playback"
        self.register_expected_event(expected_event, expected_variable,
                                     expected_variable_value, async_response)
        self.call_command('playback', path)
        event = async_response.get(block=True)
        # TODO(italo): Decide what we need to return. Returning whole event right now
        return event

    def play_and_get_digits(self, min_digits=None, max_digits=None,
                            max_attempts=None, timeout=None, terminators=None, prompt_file=None,
                            error_file=None, variable=None, digits_regex=None,
                            digit_timeout=None, transfer_on_fail=None,
                            block=True, response_timeout=30):
        args = "%s %s %s %s %s %s %s %s %s %s %s" % (min_digits, max_digits, max_attempts,
                                                  timeout, terminators, prompt_file,
                                                  error_file, variable, digits_regex,
                                                  digit_timeout, transfer_on_fail)
        if not block:
            self.call_command('play_and_get_digits', args)
            return

        async_response = gevent.event.AsyncResult()
        expected_event = "CHANNEL_EXECUTE_COMPLETE"
        expected_variable = "current_application"
        expected_variable_value = "play_and_get_digits"
        self.register_expected_event(expected_event, expected_variable,
                                     expected_variable_value, async_response)
        self.call_command('play_and_get_digits', args)
        event = async_response.get(block=True, timeout=response_timeout)
        if not event:
            return
        digit = event.headers.get('variable_%s' % variable)
        return digit

    def say(self, module_name='en', lang=None, say_type='NUMBER',
            say_method='pronounced', gender='FEMININE', text=None, block=True,
            response_timeout=30):
        if lang:
            module_name += ':%s' % lang

        args = "%s %s %s %s %s" % (module_name, say_type, say_method, gender, text)
        if not block:
            self.call_command('say', args)
            return

        async_response = gevent.event.AsyncResult()
        expected_event = "CHANNEL_EXECUTE_COMPLETE"
        expected_variable = "current_application"
        expected_variable_value = "say"
        self.register_expected_event(expected_event, expected_variable,
                                     expected_variable_value, async_response)
        self.call_command('say', args)
        event = async_response.get(block=True, timeout=response_timeout)
        return event

    def register_expected_event(self, expected_event, expected_variable,
                                expected_value, async_response):
        if expected_event not in self.expected_events:
            self.expected_events[expected_event] = []
        self.expected_events[expected_event].append((expected_variable,
                                                    expected_value,
                                                    async_response))

    def hangup(self, cause='NORMAL_CLEARING'):
        self.call_command('hangup', cause)

    def uuid_break(self):
        # TODO(italo): Properly detect when send() method should fail or not.
        # Not sure if this is the best way to avoid sending
        # session related commands, but for now it's working.
        # Another idea is to create a property called _socket_mode where the
        # values can be inbound or outbound and when running in outbound
        # mode we can make sure we'll only send a few permitted commands when
        # lingering is activated.
        if self._lingering:
            raise OutboundSessionHasGoneAway
        self.send('api uuid_break %s' % self.uuid)


class OutboundESLServer(object):
    def __init__(self, bind_address='127.0.0.1', bind_port=8000,
                 application=None, max_connections=100):
        self.bind_address = bind_address
        self.bind_port = bind_port
        self.max_connections = connection_limit
        self.connection_pool = GeventPool(max_connections)
        if not application:
            raise ValueError('You need an Application to control your calls.')
        self.application = application
        self._running = False
        logging.info('Starting OutboundESLServer at %s:%s' %
                     (self.bind_address, self.bind_port))

    def listen(self):
        self.server = socket.socket()
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.bind_address, self.bind_port))
        self.server.listen(100)
        self._running = True

        while self._running:
            if self.connection_pool.full():
                logging.info('Rejecting call, server is at full capacity, current connection count is %s/%s' %
                             (self.max_connections - self.connection_pool.free_count(), self.max_connections))
                gevent.sleep(0.1)
                continue

            sock, client_address = self.server.accept()
            session = OutboundSession(client_address, sock)
            app = self.application(session)
            handler = gevent.spawn(app.run)
            self.connection_pool.add(handler)

    def stop(self):
        self._running = False

