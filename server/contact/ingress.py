"""Secretless Unix HTTP ingress. No IP listeners, SMTP or request logging."""
import argparse
import os
import re
import sys
from common import BODY_LIMIT, RESULTS, Limiter, Reader, activated_listener, form_body, relay_call, require, serve

ORIGIN = 'https://diamaneos.de'
HEAD_LIMIT = 8192


def http_request(connection):
    reader = Reader(connection, 5)
    data = bytearray()
    while b'\r\n\r\n' not in data:
        require(len(data) < HEAD_LIMIT)
        part = reader.recv(min(1024, HEAD_LIMIT - len(data)))
        require(part)
        data.extend(part)
    head, body = bytes(data).split(b'\r\n\r\n', 1)
    require(all(c == 13 or c == 10 or 32 <= c <= 126 for c in head))
    lines = head.decode('ascii').split('\r\n')
    require(len(lines) <= 7 and lines[0] == 'POST /contact/submit HTTP/1.1')
    headers = {}
    allowed = {'host', 'origin', 'content-type', 'content-length', 'connection'}
    for line in lines[1:]:
        require(re.fullmatch(r'[A-Za-z-]+: *[\x20-\x7e]+', line))
        key, value = line.split(':', 1)
        key = key.lower()
        require(key in allowed and key not in headers)
        headers[key] = value.strip(' ')
    require(headers.get('host') == 'diamaneos.de' and headers.get('origin') == ORIGIN)
    require(headers.get('content-type', '').lower() in {
        'application/x-www-form-urlencoded', 'application/x-www-form-urlencoded; charset=utf-8'})
    require(headers.get('connection', 'close') == 'close')
    length = headers.get('content-length', '')
    require(re.fullmatch(r'[0-9]{1,5}', length))
    count = int(length)
    require(0 < count <= BODY_LIMIT and len(body) <= count)
    body += reader.exact(count - len(body))
    return form_body(body)


def response(connection, result):
    path = RESULTS.get(result, RESULTS[b'UNAVAILABLE\n'])
    connection.settimeout(2)
    connection.sendall(('HTTP/1.1 303 See Other\r\nLocation: ' + path
        + '\r\nCache-Control: no-store\r\nContent-Length: 0\r\nConnection: close\r\n\r\n').encode('ascii'))


class Ingress:
    def __init__(self, relay_socket):
        self.relay_socket = relay_socket
        self.limiter = Limiter()

    def handle(self, connection):
        result = b'INVALID\n'
        try:
            value = http_request(connection)
            if not self.limiter.take():
                result = b'RATE_LIMITED\n'
            else:
                try:
                    result = relay_call(self.relay_socket, value)
                except (OSError, ValueError):
                    result = b'UNAVAILABLE\n'
        except (OSError, ValueError):
            pass
        response(connection, result)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--relay-socket', required=True)
    args = parser.parse_args()
    try:
        require(sys.platform == 'linux' and os.getuid() == os.geteuid() != 0)
        serve(activated_listener(), Ingress(args.relay_socket).handle, 35)
    except (OSError, ValueError):
        return 78
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
