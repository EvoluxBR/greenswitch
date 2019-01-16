import greenswitch
import gevent


fs = greenswitch.InboundESL(host='127.0.0.1', port=8021, password='ClueCon')
fs.connect()

@fs.handle('sofia::unregister')
def register_failure(event):
    message = '[{Event-Date-Local}] - "{from-user}@{from-host}" unregistered.'
    print(message.format(**event.headers))


if __name__ == "__main__":
    fs.send('EVENTS PLAIN ALL')
    print('Connected to FreeSWITCH!')
    while True:
        try:
            gevent.sleep(1)
        except KeyboardInterrupt:
            fs.stop()
            break
    print('ESL Disconnected.')
