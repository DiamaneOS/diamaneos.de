"""UID-gated Unix relay with verified SMTP TLS and no persistent queue."""
import argparse
import contextlib
from email.message import EmailMessage
from email.policy import SMTP as MAIL_POLICY
import ipaddress
import os
from pathlib import Path
import pwd
import re
import smtplib
import socket
import ssl
import struct
import subprocess
import sys
import time
from common import FRAME_LIMIT, Limiter, Reader, activated_listener, email_address, exact_json, peer_uid, protected_read, require, serve, submission, systemd_credential

RESOLVE_TIMEOUT = 3
RESOLVER_SOURCE = '''import ipaddress,json,socket,sys
rows=[]
for family,kind,protocol,_,address in socket.getaddrinfo(sys.argv[1],int(sys.argv[2]),type=socket.SOCK_STREAM,proto=socket.IPPROTO_TCP):
 if family not in (socket.AF_INET,socket.AF_INET6): continue
 ip=ipaddress.ip_address(address[0])
 row=[ip.version,str(ip),address[3] if family==socket.AF_INET6 else 0]
 if row not in rows: rows.append(row)
 if len(rows)==8: break
print(json.dumps(rows,separators=(',',':')))
'''


def resolve_addresses(host, port):
    # NSS may block inside native code despite Python signal handlers. Resolve
    # in a separately timed, reaped process with no message or credential input.
    result = subprocess.run([sys.executable, '-I', '-B', '-c', RESOLVER_SOURCE,
        host, str(port)], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, timeout=RESOLVE_TIMEOUT, check=True,
        env={'LANG': 'C', 'LC_ALL': 'C'}, close_fds=True)
    require(0 < len(result.stdout) <= 4096)
    rows = exact_json(result.stdout)
    require(type(rows) is list and 1 <= len(rows) <= 8)
    for row in rows:
        require(type(row) is list and len(row) == 3 and type(row[0]) is int
                and row[0] in (4, 6) and type(row[1]) is str
                and type(row[2]) is int and 0 <= row[2] <= 0xffffffff)
        address = ipaddress.ip_address(row[1])
        require(address.version == row[0] and '%' not in row[1]
                and (row[0] == 6 or row[2] == 0))
    return rows


def resolved_socket(host, port, timeout):
    rows = resolve_addresses(host, port)
    deadline = time.monotonic() + timeout
    for version, address, scope in rows:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError()
        connection = socket.socket(socket.AF_INET if version == 4 else socket.AF_INET6,
                                   socket.SOCK_STREAM, socket.IPPROTO_TCP)
        try:
            connection.settimeout(remaining)
            connection.connect((address, port) if version == 4 else (address, port, 0, scope))
            return connection
        except OSError:
            connection.close()
        except BaseException:
            connection.close()
            raise
    raise OSError('SMTP connection unavailable')


class ResolvedSMTP(smtplib.SMTP):
    def _get_socket(self, host, port, timeout):
        return resolved_socket(host, port, timeout)


class ResolvedSMTPSSL(smtplib.SMTP_SSL):
    def __init__(self, *, context, **kwargs):
        self.tls_context = context
        super().__init__(context=context, **kwargs)

    def _get_socket(self, host, port, timeout):
        connection = resolved_socket(host, port, timeout)
        try:
            # Authenticate the configured hostname, never the resolver's IP.
            return self.tls_context.wrap_socket(connection, server_hostname=host)
        except BaseException:
            connection.close()
            raise


def configuration(path):
    value = exact_json(protected_read(path, 8192))
    require(type(value) is dict and set(value) == {'smtp_host', 'smtp_port', 'tls',
        'smtp_username', 'mail_from', 'mail_to', 'subject'})
    require(type(value['smtp_host']) is str and len(value['smtp_host']) <= 253
            and re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?', value['smtp_host']))
    require(type(value['tls']) is str and type(value['smtp_port']) is int and (value['tls'], value['smtp_port'])
            in {('ssl', 465), ('starttls', 587)})
    for key, cap in (('smtp_username', 254), ('subject', 120)):
        require(type(value[key]) is str and 0 < len(value[key]) <= cap
                and all(32 <= ord(c) <= 126 for c in value[key]))
    email_address(value['mail_from']); email_address(value['mail_to'])
    return value


def credential():
    directory = os.environ.get('CREDENTIALS_DIRECTORY')
    require(directory and Path(directory).is_absolute())
    path = Path(directory) / 'smtp-password'
    raw = (systemd_credential(path, 1025) if Path(directory).parent == Path('/run/credentials')
           else protected_read(path, 1025, secret=True))
    if raw.endswith(b'\n'):
        raw = raw[:-1]
    require(0 < len(raw) <= 1024 and all(32 <= c <= 126 for c in raw))
    return raw.decode('ascii')


def deliver(config, password, value, *, context=None):
    value = submission(value)
    message = EmailMessage(policy=MAIL_POLICY)
    message['From'] = config['mail_from']
    message['To'] = config['mail_to']
    message['Subject'] = config['subject']
    message['Reply-To'] = value['email']
    message.set_content(value['message'], cte='quoted-printable')
    tls = context if context is not None else ssl.create_default_context()
    require(tls.check_hostname and tls.verify_mode == ssl.CERT_REQUIRED)
    tls.minimum_version = ssl.TLSVersion.TLSv1_2
    client = None
    try:
        kwargs = dict(host=config['smtp_host'], port=config['smtp_port'],
                      local_hostname=config['mail_from'].split('@')[1], timeout=5)
        if config['tls'] == 'ssl':
            client = ResolvedSMTPSSL(**kwargs, context=tls)
        else:
            require(config['tls'] == 'starttls')
            client = ResolvedSMTP(**kwargs)
            require(client.ehlo()[0] == 250)
            client.starttls(context=tls)
        require(client.ehlo()[0] == 250)
        client.login(config['smtp_username'], password)
        require(client.sendmail(config['mail_from'], [config['mail_to']], message.as_bytes()) == {})
        return b'SENT\n'
    except (OSError, ValueError, subprocess.SubprocessError):
        return b'UNAVAILABLE\n'
    finally:
        if client is not None:
            with contextlib.suppress(OSError):
                client.close()


class Relay:
    def __init__(self, ingress_uid, config, password):
        self.ingress_uid = ingress_uid
        self.config = config
        self.password = password
        self.limiter = Limiter(capacity=3, interval=300)

    def handle(self, connection):
        result = b'INVALID\n'
        try:
            require(peer_uid(connection) == self.ingress_uid)
            if not self.limiter.take():
                result = b'RATE_LIMITED\n'
            else:
                reader = Reader(connection, 5)
                size = struct.unpack('!I', reader.exact(4))[0]
                require(0 < size <= FRAME_LIMIT)
                value = submission(exact_json(reader.exact(size)))
                require(reader.recv(1) == b'')
                result = deliver(self.config, self.password, value)
        except (OSError, ValueError):
            pass
        connection.settimeout(2)
        connection.sendall(result)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    parser.add_argument('--ingress-user', required=True)
    args = parser.parse_args()
    try:
        require(sys.platform == 'linux' and os.getuid() == os.geteuid() != 0)
        uid = pwd.getpwnam(args.ingress_user).pw_uid
        require(0 < uid < 65534 and uid != os.geteuid())
        app = Relay(uid, configuration(args.config), credential())
        serve(activated_listener(), app.handle, 25)
    except (OSError, ValueError, KeyError):
        return 78
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
