"""Bounded contact protocol shared by the two separate processes."""
import errno
import json
import os
from pathlib import Path
import re
import signal
import socket
import stat
import struct
import time
import unicodedata
from urllib.parse import parse_qsl

BODY_LIMIT = 65536
FRAME_LIMIT = 20000
RESULTS = {b'SENT\n': '/contact/sent/', b'INVALID\n': '/contact/invalid/',
           b'UNAVAILABLE\n': '/contact/unavailable/', b'RATE_LIMITED\n': '/contact/rate-limited/'}


class Invalid(ValueError):
    pass


def require(condition):
    if not condition:
        raise Invalid()


def email_address(value):
    require(type(value) is str and value.isascii() and len(value) <= 254)
    parts = value.split('@')
    require(len(parts) == 2)
    local, domain = parts
    atom = r"[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+"
    require(len(local) <= 64 and re.fullmatch(atom + r'(?:\.' + atom + r')*', local))
    labels = domain.split('.')
    require(len(labels) >= 2 and len(domain) <= 253 and all(
        re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?', label)
        for label in labels))
    return value


def submission(value):
    require(type(value) is dict and set(value) == {'email', 'message'})
    email_address(value['email'])
    message = value['message']
    require(type(message) is str)
    message = message.replace('\r\n', '\n')
    require(1 <= len(message) <= 4000 and message.strip())
    require(not any(c not in '\n\t' and unicodedata.category(c) in {'Cc', 'Cf', 'Cs'} for c in message))
    return {'email': value['email'], 'message': message}


def form_body(body):
    require(0 < len(body) <= BODY_LIMIT)
    text = body.decode('ascii')
    require(not re.search(r'%(?![0-9a-fA-F]{2})', text))
    pairs = parse_qsl(text, keep_blank_values=True, strict_parsing=True,
                     encoding='utf-8', errors='strict', max_num_fields=2)
    require(len(pairs) == 2 and {key for key, _ in pairs} == {'email', 'message'})
    return submission(dict(pairs))


def exact_json(body):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result)
            result[key] = value
        return result
    try:
        return json.loads(body.decode('utf-8'), object_pairs_hook=unique,
                          parse_constant=lambda _: (_ for _ in ()).throw(Invalid()))
    except RecursionError:
        raise Invalid() from None


class Reader:
    def __init__(self, connection, seconds):
        self.connection = connection
        self.deadline = time.monotonic() + seconds

    def recv(self, count):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError()
        self.connection.settimeout(remaining)
        return self.connection.recv(count)

    def exact(self, count):
        data = bytearray()
        while len(data) < count:
            part = self.recv(count - len(data))
            require(part)
            data.extend(part)
        return bytes(data)


class Limiter:
    """Five initial attempts, then one per twenty seconds; no client records."""
    def __init__(self, clock=time.monotonic, *, capacity=5, interval=20):
        require(type(capacity) is int and 1 <= capacity <= 5
                and type(interval) is int and 20 <= interval <= 300)
        self.clock = clock
        self.capacity = capacity
        self.interval = interval
        self.tokens = float(capacity)
        self.updated = clock()

    def take(self):
        now = self.clock()
        self.tokens = min(float(self.capacity), self.tokens + max(0, now - self.updated) / self.interval)
        self.updated = now
        if self.tokens < 1:
            return False
        self.tokens -= 1
        return True


def relay_call(path, value):
    payload = json.dumps(submission(value), ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    require(len(payload) <= FRAME_LIMIT)
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(25)
        connection.connect(path)
        write_complete = False
        try:
            connection.sendall(struct.pack('!I', len(payload)) + payload)
            connection.shutdown(socket.SHUT_WR)
            write_complete = True
        except OSError as error:
            # UID/rate refusal can close before the caller finishes writing.
            # Consume only a bounded failure reply and never infer delivery here.
            if error.errno not in {errno.EPIPE, errno.ENOTCONN, errno.ECONNRESET}:
                raise
        reader = Reader(connection, 25)
        result = bytearray()
        while True:
            part = reader.recv(17 - len(result))
            if not part:
                break
            result.extend(part)
            require(len(result) <= 16)
        require(bytes(result) in RESULTS and (write_complete or bytes(result) != b'SENT\n'))
        return bytes(result)


def peer_uid(connection):
    require(hasattr(socket, 'SO_PEERCRED'))
    return struct.unpack('3i', connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))[1]


def protected_read(path, cap, *, secret=False):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_uid in {0, os.geteuid()}
                and info.st_nlink == 1 and not info.st_mode & (0o077 if secret else 0o022)
                and 0 < info.st_size <= cap)
        body = stream.read(cap + 1)
        require(len(body) == info.st_size)
        return body


def systemd_credential(path, cap):
    directory = os.environ.get('CREDENTIALS_DIRECTORY')
    root = Path(directory) if directory else None
    require(root is not None and root.is_absolute() and root.parent == Path('/run/credentials')
            and root.name.endswith('.service') and Path(path).parent == root)
    parent = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        info = os.fstat(parent)
        require(info.st_uid == info.st_gid == 0 and stat.S_ISDIR(info.st_mode)
                and stat.S_IMODE(info.st_mode) == 0o550)
        handle = os.open(Path(path).name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        with os.fdopen(handle, 'rb') as stream:
            info = os.fstat(stream.fileno())
            require(stat.S_ISREG(info.st_mode) and info.st_uid == info.st_gid == 0
                    and info.st_nlink == 1 and stat.S_IMODE(info.st_mode) == 0o440
                    and 0 < info.st_size <= cap)
            body = stream.read(cap + 1)
            require(len(body) == info.st_size)
            return body
    finally:
        os.close(parent)


def activated_listener():
    require(os.environ.get('LISTEN_PID') == str(os.getpid()) and os.environ.get('LISTEN_FDS') == '1')
    listener = socket.socket(fileno=3)
    require(listener.family == socket.AF_UNIX and listener.type == socket.SOCK_STREAM
            and listener.getsockopt(socket.SOL_SOCKET, socket.SO_ACCEPTCONN) == 1)
    listener.settimeout(None)
    return listener


def serve(listener, handler, seconds):
    # The single main-thread worker gives a whole-request deadline, including
    # SMTP multiline responses and clients that send one byte at a time.
    # Native resolver calls have their own supervised subprocess deadline.
    def expire(*_):
        raise TimeoutError()
    signal.signal(signal.SIGALRM, expire)
    with listener:
        while True:
            connection, _ = listener.accept()
            with connection:
                signal.setitimer(signal.ITIMER_REAL, seconds)
                try:
                    handler(connection)
                except (OSError, ValueError):
                    pass
                finally:
                    signal.setitimer(signal.ITIMER_REAL, 0)
