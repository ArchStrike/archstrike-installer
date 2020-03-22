
import socket
import ssl
from .config import *


logger = setup_logger(__name__)


class LogHandler(object):

    def __init__(self, nick, logs):
        self.server = IRC_SERVER
        self.port = IRC_PORT
        self.bot_nick = IRC_BOT_NICK
        self.nick = nick

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
        base_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        base_sock.settimeout(30)
        # Setup SSL Socket
        self.sock = context.wrap_socket(base_sock, server_hostname=self.server)
        self.sock.connect((self.server, self.port))
        try:
            notice = self.sock.recv(1024)
            if b'NOTICE' in notice:
                logger.info('Squelched IRC NOTICE message from freenode...')
        except socket.timeout:
            pass  # RFC-2812 suggests not waiting forever
        self.send(f'USER {self.nick} 8 * :ArchStrike Installer')
        self.send(f'NICK {self.nick}')

        # RECEIVE IRC Server Info
        while True:
            data = self.sock.recv(1024)
            if b'End of /MOTD command.' in data:
                logger.info('Squelched IRC MOTD message from freenode...')
                break

    def send_logs(self, links):
        logs = ' '.join(links)
        self.send('PRIVMSG {0} :.asinstaller {1}'.format(self.bot_nick, logs))

    def disconnect(self):
        self.send('QUIT')
        self.sock.close()
