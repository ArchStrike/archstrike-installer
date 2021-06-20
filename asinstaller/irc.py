import socket
import ssl
from .config import IRC_BOT_NICK, IRC_PORT, IRC_SERVER, get_logger

__all__ = ["LogHandler"]
logger = get_logger(__name__)


class LogHandler(object):

    def __init__(self, nick, logs):
        self.server = IRC_SERVER
        self.port = IRC_PORT
        self.bot_nick = IRC_BOT_NICK
        self.nick = nick  # freenode truncates at 16 characters

        self.sock = None
        self.connect()
        self.send_logs(logs)
        self.disconnect()

    def send(self, msg):
        self.sock.sendall(f'{msg}\r\n'.encode())

    def connect(self):
        # Create context for verifying host
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        context.verify_mode = ssl.CERT_REQUIRED
        context.check_hostname = True
        context.load_default_certs()
        # Create a socket
        self.base_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.base_sock.settimeout(30)
        # Setup SSL Socket
        self.sock = context.wrap_socket(self.base_sock, server_hostname=self.server)
        self.sock.connect((self.server, self.port))
        try:
            notice = self.sock.recv(1024)
            if b'NOTICE' in notice:
                logger.info('Squelched IRC NOTICE message from freenode...')
            else:
                logger.info(f'Expected NOTICE response from freenode, but received: {notice}')
        except socket.timeout:
            logger.info('Receive for NOTICE timed out...')
            pass  # RFC-2812 suggests not waiting forever
        self.send(f'USER {self.nick} 8 * :ArchStrike Installer')
        self.send(f'NICK {self.nick}')

        # RECEIVE IRC Server Info
        data = ''
        while True:  # sock.recv will eventually timeout in failure conditions preventing infinite loop
            data += self.sock.recv(1024).decode().rstrip()
            if 'End of /MOTD command.' in data:
                logger.info('Squelched IRC MOTD message from freenode...')
            if '+Zi' in data:
                # Wait for MODE to indicate securely connected to avoid sending PING and receiving MODE prior to PONG
                break
        # Double check freenode is reachable
        try:
            self.send(f'PING {self.server}')
            data = self.sock.recv(1024)
            if b'PONG' in data:
                logger.info('PING-PONG successful')
            else:
                logger.info(f'Expected PONG response from freenode, but received: {data}')
        except socket.timeout:
            # RFC-2812 suggests not waiting forever
            logger.info('Receive for PING timed out...')

    def send_logs(self, links):
        logs = ' '.join(links)
        self.send('PRIVMSG {0} :.asinstaller {1}'.format(self.bot_nick, logs))

    def disconnect(self):
        self.send('QUIT')
        self.sock.close()
