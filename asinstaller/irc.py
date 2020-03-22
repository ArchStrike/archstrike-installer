
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
        self.sock.sendall('{0}\r\n'.format(msg))

    def connect(self):
        # Create context for verifying host
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        context.verify_mode = ssl.CERT_REQUIRED
        context.check_hostname = True
        context.load_default_certs()
        # Create a socket
        base_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        base_sock.settimeout(10)
        # Setup SSL Socket
        self.sock = context.wrap_socket(base_sock,
                                        server_hostname=self.server)
        self.sock.connect((self.server, self.port))

        self.send('NICK {0}'.format(self.nick))
        self.send('USER {0} 8 * :ArchStrike Installer'.format(self.nick))

        # RECEIVE IRC Server Info
        while True:
            try:
                data = self.sock.recv(1024)
            except ssl.SSLError:
                break

    def send_logs(self, links):
        logs = ' '.join(links)
        self.send('PRIVMSG {0} :.asinstaller {1}'.format(self.bot_nick, logs))

    def disconnect(self):
        self.send('QUIT')
        self.sock.close()
