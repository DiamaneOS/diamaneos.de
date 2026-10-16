"""Contact tests: local Unix/loopback only, disposable TLS and fake credentials."""
import contextlib
import errno
from email import policy
from email.parser import BytesParser
import io
import json
import os
from pathlib import Path
import socket
import ssl
import struct
import subprocess
import sys
import tempfile
import threading
import time
import types
import unittest
from unittest.mock import patch
from urllib.parse import urlencode

CONTACT = Path(__file__).resolve().parents[1] / 'server/contact'
sys.path.insert(0, str(CONTACT))
import common
import ingress
import relay

VALUE = {'email': 'reader+contact@example.invalid', 'message': 'Hello ' + chr(0xe9) + ' ' + chr(0x1f642)}
CONFIG = json.loads((CONTACT / 'relay.example.json').read_text())
PASSWORD = 'synthetic-test-only'


def request(body=None, *, method='POST', path='/contact/submit', headers=None):
    if body is None:
        body = urlencode(VALUE).encode('ascii')
    values = [('Host', 'diamaneos.de'), ('Origin', ingress.ORIGIN),
              ('Content-Type', 'application/x-www-form-urlencoded'), ('Content-Length', str(len(body)))]
    if headers is not None:
        values = headers
    return (f'{method} {path} HTTP/1.1\r\n' + ''.join(f'{k}: {v}\r\n' for k, v in values)
            + '\r\n').encode('ascii') + body


class LocalServer:
    def __init__(self, family, address, handler):
        self.listener = socket.socket(family, socket.SOCK_STREAM)
        self.listener.bind(address)
        self.listener.listen(8)
        self.address = self.listener.getsockname()
        self.listener.settimeout(0.1)
        self.handler = handler
        self.errors = []
        self.stopped = threading.Event()
        self.thread = threading.Thread(target=self.loop)

    def loop(self):
        while not self.stopped.is_set():
            try:
                connection, _ = self.listener.accept()
            except (TimeoutError, socket.timeout):
                continue
            except OSError:
                break
            with connection:
                try:
                    self.handler(connection)
                except BaseException as error:
                    self.errors.append(type(error).__name__)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.stopped.set()
        self.listener.close()
        self.thread.join(4)
        if self.thread.is_alive():
            raise AssertionError('local fixture did not stop')
        if self.errors:
            raise AssertionError('local fixture failed: ' + ','.join(self.errors))


def exchange(family, address, data):
    with socket.socket(family, socket.SOCK_STREAM) as connection:
        connection.settimeout(3)
        connection.connect(address)
        connection.sendall(data)
        try:
            connection.shutdown(socket.SHUT_WR)
        except OSError as error:
            if error.errno not in {errno.ENOTCONN, errno.EPIPE}:
                raise
        output = bytearray()
        while True:
            part = connection.recv(4096)
            if not part:
                return bytes(output)
            output.extend(part)
            if len(output) > 8192:
                raise AssertionError('unbounded local reply')


def wire(value):
    payload = json.dumps(value, ensure_ascii=False).encode()
    return struct.pack('!I', len(payload)) + payload


class ValidationTests(unittest.TestCase):
    def test_utf8_and_unicode_character_bound(self):
        self.assertEqual(VALUE, common.form_body(urlencode(VALUE).encode()))
        for character in ('a', chr(0x1f642)):
            value = dict(VALUE, message=character * 4000)
            self.assertEqual(value, common.form_body(urlencode(value).encode()))
            with self.assertRaises(common.Invalid): common.submission(dict(value, message=character * 4001))

    def test_ascii_addr_spec_rejects_headers_display_names_and_bad_domains(self):
        for email in ('x@example.invalid\r\nBcc: other@example.invalid', 'Name <a@example.invalid>',
                      'a@example.invalid,b@example.invalid', 'é@example.invalid', 'a@é.invalid',
                      '.a@example.invalid', 'a..b@example.invalid', 'a.@example.invalid',
                      'a@-example.invalid', 'a@example..invalid', 'a@localhost', 'a@ex_ample.invalid',
                      'a' * 65 + '@example.invalid', 'a@example.invalid\x00'):
            with self.subTest(email=email), self.assertRaises(common.Invalid): common.email_address(email)
        for email in ('a.b+tag@example.invalid', "o'hara@example.invalid"):
            self.assertEqual(email, common.email_address(email))

    def test_controls_empty_wrong_types_and_unrecognised_fields_refuse(self):
        values = [dict(VALUE, message=''), dict(VALUE, message='   '), dict(VALUE, message=7),
                  dict(VALUE, email=[]), dict(VALUE, recipient='elsewhere@example.invalid'),
                  {'message': 'only'}, []]
        values += [dict(VALUE, message='text' + c) for c in ('\r', '\x00', '\x01', '\x0b', '\x7f', '\u202e', '\ud800')]
        for value in values:
            with self.subTest(value_type=type(value).__name__), self.assertRaises(common.Invalid):
                common.submission(value)

    def test_multiline_tabs_and_crlf_normalize_without_mutating_input(self):
        text = 'First\r\n\r\n\tIndented\nLast'
        value = dict(VALUE, message=text)
        expected = dict(value, message='First\n\n\tIndented\nLast')
        self.assertEqual(expected, common.submission(value))
        self.assertEqual(expected, common.form_body(urlencode(value).encode()))
        self.assertEqual(text, value['message'])
        self.assertEqual(expected, common.submission(expected))
        at_limit = dict(VALUE, message='x\r\n' * 2000)
        self.assertEqual(4000, len(common.form_body(urlencode(at_limit).encode())['message']))
        with self.assertRaises(ValueError): common.submission(dict(at_limit, message=at_limit['message'] + 'x'))

    def test_urlencoding_duplicates_unknown_fields_percent_and_utf8_refuse(self):
        for body in (b'email=a%40example.invalid&message=hello&message=again',
                     b'email=a%40example.invalid&email=b%40example.invalid',
                     b'email=a%40example.invalid&subject=hello', b'email=a%40example.invalid&message',
                     b'email=a%40example.invalid&message=%', b'email=a%40example.invalid&message=%GG',
                     b'email=a%40example.invalid&message=%ff', b'email=a%40example.invalid&message=%C0%AF',
                     b'email=a%40example.invalid&message=\xff', b'x' * 65537):
            with self.subTest(length=len(body)), self.assertRaises(ValueError): common.form_body(body)

    def test_relay_json_rejects_duplicate_nested_and_nonfinite_values(self):
        for body in (b'{"email":"a@example.invalid","message":"one","message":"two"}',
                     b'{"email":"a@example.invalid","message":NaN}', b'{"email":"a@example.invalid","message":{}}',
                     b'[' * 2000 + b'0' + b']' * 2000):
            with self.assertRaises(ValueError): common.submission(common.exact_json(body))

    def test_global_limiter_has_constant_memory_and_bounded_refill(self):
        clock = [100.0]
        limit = common.Limiter(lambda: clock[0])
        self.assertTrue(all(limit.take() for _ in range(5)))
        self.assertFalse(limit.take())
        clock[0] += 19; self.assertFalse(limit.take())
        clock[0] += 1; self.assertTrue(limit.take()); self.assertFalse(limit.take())
        clock[0] += 100000
        self.assertTrue(all(limit.take() for _ in range(5))); self.assertFalse(limit.take())
        self.assertEqual({'clock', 'tokens', 'updated', 'capacity', 'interval'}, set(vars(limit)))

    def test_relay_budget_has_three_attempts_then_one_per_five_minutes(self):
        clock=[0.0];limit=common.Limiter(lambda:clock[0],capacity=3,interval=300)
        self.assertTrue(all(limit.take() for _ in range(3)));self.assertFalse(limit.take())
        clock[0]=299;self.assertFalse(limit.take())
        clock[0]=300;self.assertTrue(limit.take());self.assertFalse(limit.take())
        for value in (0,6,True):
            with self.assertRaises(ValueError):common.Limiter(capacity=value)
        for value in (0,301,True):
            with self.assertRaises(ValueError):common.Limiter(interval=value)


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.app = ingress.Ingress('/not-a-live-relay.sock')

    def check(self, raw):
        with LocalServer(socket.AF_INET, ('127.0.0.1', 0), self.app.handle) as server:
            return exchange(socket.AF_INET, server.address, raw)

    def test_actual_loopback_http_success_uses_fixed_empty_redirect(self):
        with patch.object(ingress, 'relay_call', return_value=b'SENT\n') as forward:
            output = self.check(request())
        self.assertIn(b'303 See Other\r\nLocation: /contact/sent/\r\n', output)
        self.assertIn(b'Cache-Control: no-store', output)
        self.assertTrue(output.endswith(b'\r\n\r\n'))
        self.assertNotIn(VALUE['email'].encode(), output)
        forward.assert_called_once_with(self.app.relay_socket, VALUE)

    def test_methods_targets_origin_and_http_version_never_forward(self):
        good = [('Host', 'diamaneos.de'), ('Origin', ingress.ORIGIN),
                ('Content-Type', 'application/x-www-form-urlencoded'), ('Content-Length', '1')]
        cases = [request(method=m) for m in ('GET', 'HEAD', 'PUT', 'OPTIONS', 'TRACE')]
        cases += [request(path=p) for p in ('/', '/contact/submit?x=1', 'https://diamaneos.de/contact/submit')]
        cases += [request(b'x', headers=[(k, origin if k == 'Origin' else v) for k, v in good])
                  for origin in ('null', '', 'http://diamaneos.de', 'https://diamaneos.de.evil.invalid',
                                 'https://diamaneos.de/', 'https://other.invalid', ingress.ORIGIN + ', ' + ingress.ORIGIN)]
        cases += [request().replace(b'HTTP/1.1', b'HTTP/1.0')]
        for raw in cases:
            with self.subTest(length=len(raw)), patch.object(ingress, 'relay_call') as forward:
                self.assertIn(b'/contact/invalid/', self.check(raw)); forward.assert_not_called()

    def test_duplicate_unknown_forwarded_and_smuggling_headers_refuse(self):
        raw = request()
        for line in (b'Origin: https://diamaneos.de\r\n', b'Content-Length: 0\r\n',
                     b'Transfer-Encoding: chunked\r\n', b'X-Forwarded-For: 127.0.0.1\r\n',
                     b'Forwarded: for=127.0.0.1\r\n', b'Authorization: secret\r\n',
                     b' Cookie: folded\r\n', b'Origin : https://diamaneos.de\r\n', b'X: bad\x00\r\n'):
            with self.subTest(line_type=line.split(b':')[0]), patch.object(ingress, 'relay_call') as forward:
                broken = raw.replace(b'\r\n\r\n', b'\r\n' + line + b'\r\n')
                self.assertIn(b'/contact/invalid/', self.check(broken)); forward.assert_not_called()

    def test_missing_headers_types_body_lengths_controls_and_caps_refuse(self):
        raw = request()
        cases = [raw.replace(b'application/x-www-form-urlencoded', x) for x in
                 (b'application/json', b'text/plain', b'multipart/form-data', b'application/x-www-form-urlencoded; charset=latin1')]
        cases += [raw.replace(b'Host: diamaneos.de\r\n', b''), raw.replace(b'Host: diamaneos.de', b'Host: other.invalid'),
                  raw.replace(b'Origin: https://diamaneos.de\r\n', b''),
                  raw.replace(b'Content-Length:', b'content-length:\t'),
                  request(b'x', headers=[('Host', 'diamaneos.de'), ('Origin', ingress.ORIGIN),
                      ('Content-Type', 'application/x-www-form-urlencoded'), ('Content-Length', '65537')]),
                  raw + b'EXTRA', raw[:-1], b'x' * 8192, raw.replace(b'\r\n', b'\n'),
                  request(urlencode(dict(VALUE, message='body\x00control')).encode())]
        for broken in cases:
            with self.subTest(length=len(broken)), patch.object(ingress, 'relay_call') as forward:
                self.assertIn(b'/contact/invalid/', self.check(broken)); forward.assert_not_called()

    def test_upstream_failure_and_global_overload_never_claim_sent(self):
        for result, path in common.RESULTS.items():
            self.app.limiter = common.Limiter()
            with patch.object(ingress, 'relay_call', return_value=result):
                self.assertIn(path.encode(), self.check(request()))
        self.app.limiter = common.Limiter()
        with patch.object(ingress, 'relay_call', side_effect=TimeoutError()) as forward:
            for _ in range(5): self.assertIn(b'/contact/unavailable/', self.check(request()))
            self.assertIn(b'/contact/rate-limited/', self.check(request()))
            self.assertEqual(5, forward.call_count)

    def test_absolute_socket_deadline_does_not_reset_after_partial_receive(self):
        connection = unittest.mock.Mock()
        with patch.object(common.time, 'monotonic', side_effect=[100, 101, 104, 105]):
            reader = common.Reader(connection, 5)
            connection.recv.return_value = b'x'
            reader.recv(1); reader.recv(1)
            with self.assertRaises(TimeoutError): reader.recv(1)
        self.assertEqual([unittest.mock.call(4), unittest.mock.call(1)], connection.settimeout.call_args_list)

    def test_missing_relay_is_actual_unavailable_without_pii(self):
        with tempfile.TemporaryDirectory(prefix='contact-absent-') as directory:
            self.app.relay_socket = str(Path(directory) / 'absent.sock')
            output = self.check(request())
        self.assertIn(b'Location: /contact/unavailable/', output)
        self.assertNotIn(VALUE['email'].encode(), output)
        self.assertNotIn(b'/contact/sent/', output)

    def test_inherited_unix_listener_has_real_whole_request_deadline(self):
        script = '''import os,socket,sys,time
sys.path.insert(0,sys.argv[1])
import common
fd=int(sys.argv[2])
if fd!=3: os.dup2(fd,3);os.close(fd)
os.environ['LISTEN_PID']=str(os.getpid())
os.environ['LISTEN_FDS']='1'
count=0
def handle(connection):
 global count
 count+=1
 if count==1:
  time.sleep(10)
  connection.sendall(b'SENT')
 else: connection.sendall(b'OK')
# SO_ACCEPTCONN on Unix sockets is not implemented by macOS. Keep the
# production Linux activation guard unchanged and test its deadline locally.
listener=common.activated_listener() if sys.platform=='linux' else socket.socket(fileno=3)
common.serve(listener,handle,0.1)
'''
        with tempfile.TemporaryDirectory(prefix='contact-deadline-') as directory:
            path = str(Path(directory) / 'http.sock')
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
                listener.bind(path); listener.listen(2)
                child = subprocess.Popen([sys.executable, '-I', '-B', '-c', script,
                    str(CONTACT), str(listener.fileno())], pass_fds=(listener.fileno(),),
                    env={}, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                try:
                    started = time.monotonic()
                    self.assertEqual(b'', exchange(socket.AF_UNIX, path, b''))
                    self.assertLess(time.monotonic() - started, 2)
                    self.assertEqual(b'OK', exchange(socket.AF_UNIX, path, b''))
                finally:
                    child.terminate()
                    try: output, errors = child.communicate(timeout=2)
                    except subprocess.TimeoutExpired:
                        child.kill(); output, errors = child.communicate(timeout=2)
                self.assertEqual(b'', output); self.assertEqual(b'', errors)


class UnixProtocolTests(unittest.TestCase):
    def test_early_peer_close_preserves_failure_but_never_claims_delivery(self):
        for result in common.RESULTS:
            connection = unittest.mock.MagicMock()
            connection.__enter__.return_value = connection
            connection.shutdown.side_effect = OSError(errno.ENOTCONN, 'closed')
            connection.recv.side_effect = [result, b'']
            with patch.object(common.socket, 'socket', return_value=connection):
                if result == b'SENT\n':
                    with self.assertRaises(ValueError): common.relay_call('/fixture.sock', VALUE)
                else:
                    self.assertEqual(result, common.relay_call('/fixture.sock', VALUE))

    def test_exact_reply_protocol_rejects_truncation_extra_data_and_pii(self):
        with tempfile.TemporaryDirectory(prefix='contact-test-') as directory:
            path = str(Path(directory) / 'relay.sock')
            for data in (b'', b'SENT', b'SENT\nEXTRA', b'SENT\nSENT\n', b'{"status":"sent"}',
                         b'SENT\n' + b'x' * 40, VALUE['email'].encode()):
                def handler(connection):
                    while connection.recv(4096): pass
                    connection.sendall(data)
                with LocalServer(socket.AF_UNIX, path, handler), self.assertRaises(ValueError):
                    common.relay_call(path, VALUE)
                Path(path).unlink()

    def test_request_frame_binds_only_email_and_message_and_exact_result(self):
        observed = []
        def handler(connection):
            reader = common.Reader(connection, 2)
            size = struct.unpack('!I', reader.exact(4))[0]
            observed.append(common.exact_json(reader.exact(size)))
            self.assertEqual(b'', reader.recv(1))
            connection.sendall(b'SENT\n')
        with tempfile.TemporaryDirectory(prefix='contact-test-') as directory:
            path = str(Path(directory) / 'relay.sock')
            with LocalServer(socket.AF_UNIX, path, handler):
                self.assertEqual(b'SENT\n', common.relay_call(path, VALUE))
        self.assertEqual([VALUE], observed)

    def test_relay_refuses_foreign_uid_before_parsing_or_smtp(self):
        app = relay.Relay(1234, CONFIG, PASSWORD)
        with tempfile.TemporaryDirectory(prefix='contact-test-') as directory:
            path = str(Path(directory) / 'relay.sock')
            for uid in (0, 1235, os.getuid()):
                with patch.object(relay, 'peer_uid', return_value=uid), patch.object(relay, 'deliver') as deliver:
                    with LocalServer(socket.AF_UNIX, path, app.handle):
                        # No body: refusal must precede any attacker-controlled read.
                        self.assertEqual(b'INVALID\n', exchange(socket.AF_UNIX, path, b''))
                    deliver.assert_not_called()
                Path(path).unlink()

    def test_exact_framing_and_schema_refuse_before_delivery(self):
        app = relay.Relay(1234, CONFIG, PASSWORD)
        duplicate = b'{"email":"a@example.invalid","message":"a","message":"b"}'
        cases = [struct.pack('!I', n) for n in (0, 20001, 4294967295)]
        cases += [b'\x00', struct.pack('!I', 5) + b'{}', wire(VALUE) + b'extra',
                  wire(dict(VALUE, recipient='elsewhere@example.invalid')),
                  struct.pack('!I', len(duplicate)) + duplicate]
        deep = b'[' * 2000 + b'0' + b']' * 2000
        cases.append(struct.pack('!I', len(deep)) + deep)
        with tempfile.TemporaryDirectory(prefix='contact-test-') as directory:
            path = str(Path(directory) / 'relay.sock')
            for data in cases:
                app.limiter = common.Limiter()
                with patch.object(relay, 'peer_uid', return_value=1234), patch.object(relay, 'deliver') as deliver:
                    with LocalServer(socket.AF_UNIX, path, app.handle):
                        try:
                            self.assertEqual(b'INVALID\n', exchange(socket.AF_UNIX, path, data))
                        except ConnectionResetError as error:
                            # Linux can reset a refused stream with unread bytes.
                            # Only this negative case accepts that refusal. The
                            # SMTP call must still be absent after cleanup.
                            self.assertEqual(errno.ECONNRESET, error.errno)
                    deliver.assert_not_called()
                Path(path).unlink()

    def test_linux_uid_extraction_and_unsupported_platform_fail_closed(self):
        connection = unittest.mock.Mock()
        connection.getsockopt.return_value = struct.pack('3i', 4321, 1234, 5678)
        with patch.object(common.socket, 'SO_PEERCRED', 17, create=True):
            self.assertEqual(1234, common.peer_uid(connection))
        connection, other = socket.socketpair()
        with connection, other:
            if not hasattr(socket, 'SO_PEERCRED'):
                with self.assertRaises(common.Invalid): common.peer_uid(connection)
            else:
                self.assertEqual(os.getuid(), common.peer_uid(connection))

    def test_relay_global_overload_bounds_actual_unix_requests(self):
        app = relay.Relay(1234, CONFIG, PASSWORD)
        with tempfile.TemporaryDirectory(prefix='contact-test-') as directory:
            path = str(Path(directory) / 'relay.sock')
            with (patch.object(relay, 'peer_uid', return_value=1234),
                  patch.object(relay, 'deliver', return_value=b'SENT\n') as deliver,
                  LocalServer(socket.AF_UNIX, path, app.handle)):
                for _ in range(3): self.assertEqual(b'SENT\n', exchange(socket.AF_UNIX, path, wire(VALUE)))
                self.assertEqual(b'RATE_LIMITED\n', exchange(socket.AF_UNIX, path, b''))
                self.assertEqual(3, deliver.call_count)


class ConfigurationTests(unittest.TestCase):
    def test_protected_config_is_exact_and_tls_pair_is_fixed(self):
        with tempfile.TemporaryDirectory(prefix='contact-config-') as directory:
            path = Path(directory) / 'relay.json'
            def write(value):
                path.write_text(json.dumps(value)); path.chmod(0o600)
            write(CONFIG); self.assertEqual(CONFIG, relay.configuration(path))
            for changed in (dict(CONFIG, tls='plain', smtp_port=25), dict(CONFIG, tls='ssl', smtp_port=587),
                            dict(CONFIG, tls='starttls', smtp_port=465), dict(CONFIG, smtp_port=True),
                            dict(CONFIG, tls=[]), dict(CONFIG, smtp_host='host:465'),
                            dict(CONFIG, subject='contact\r\nBcc: victim'), dict(CONFIG, secret='password'),
                            dict(CONFIG, mail_to='name <someone@example.invalid>')):
                write(changed)
                with self.assertRaises(ValueError): relay.configuration(path)
            write(dict(CONFIG, tls='starttls', smtp_port=587))
            self.assertEqual('starttls', relay.configuration(path)['tls'])
            path.chmod(0o666)
            with self.assertRaises(ValueError): relay.configuration(path)
            path.unlink(); path.symlink_to(CONTACT / 'relay.example.json')
            with self.assertRaises(OSError): relay.configuration(path)

    def test_credential_has_no_password_environment_fallback_and_is_private(self):
        with patch.dict(os.environ, {'SMTP_PASSWORD': PASSWORD}, clear=True), self.assertRaises(ValueError):
            relay.credential()
        with tempfile.TemporaryDirectory(prefix='contact-credential-') as directory:
            path = Path(directory) / 'smtp-password'
            with patch.dict(os.environ, {'CREDENTIALS_DIRECTORY': directory}, clear=True):
                with self.assertRaises(OSError): relay.credential()
                for raw in (b'', b'p\r\nx', b'\xff', b'x' * 1026):
                    path.write_bytes(raw); path.chmod(0o600)
                    with self.assertRaises(ValueError): relay.credential()
                path.write_bytes(PASSWORD.encode() + b'\n'); path.chmod(0o600)
                self.assertEqual(PASSWORD, relay.credential())
                path.chmod(0o644)
                with self.assertRaises(ValueError): relay.credential()
                path.chmod(0o600); os.link(path, Path(directory) / 'extra')
                with self.assertRaises(ValueError): relay.credential()

    def test_native_credential_scope_does_not_widen_generic_secret_files(self):
        with patch.dict(os.environ, {'CREDENTIALS_DIRECTORY':'/tmp/credentials'}, clear=True), self.assertRaises(ValueError):
            common.systemd_credential('/tmp/credentials/smtp-password',1025)
        with patch.dict(os.environ, {'CREDENTIALS_DIRECTORY':'/run/credentials/contact-relay.service'}, clear=True):
            with self.assertRaises(ValueError):common.systemd_credential('/run/credentials/other.service/smtp-password',1025)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'smtp-password';path.write_bytes(PASSWORD.encode());path.chmod(0o440)
            with self.assertRaises(ValueError):common.protected_read(path,1025,secret=True)

    def test_main_refuses_root_same_uid_or_missing_assets_before_listener(self):
        args = ['relay.py', '--config', '/absent-contact-test.json', '--ingress-user', 'fake-ingress']
        for uid, peer in ((0, 1234), (502, 502), (502, 0), (502, 1234)):
            with (patch.object(sys, 'argv', args), patch.object(sys, 'platform', 'linux'),
                  patch.object(os, 'getuid', return_value=uid), patch.object(os, 'geteuid', return_value=uid),
                  patch.object(relay.pwd, 'getpwnam', return_value=types.SimpleNamespace(pw_uid=peer)),
                  patch.object(relay, 'activated_listener') as listener):
                self.assertEqual(78, relay.main()); listener.assert_not_called()

    def test_socket_activation_rejects_wrong_pid_fd_count_and_family(self):
        for environment in ({}, {'LISTEN_PID': '1', 'LISTEN_FDS': '1'},
                            {'LISTEN_PID': str(os.getpid()), 'LISTEN_FDS': '2'}):
            with patch.dict(os.environ, environment, clear=True), patch.object(common.socket, 'socket') as create:
                with self.assertRaises(ValueError): common.activated_listener()
                create.assert_not_called()
        with (patch.dict(os.environ, {'LISTEN_PID': str(os.getpid()), 'LISTEN_FDS': '1'}, clear=True),
              patch.object(common.socket, 'socket', return_value=types.SimpleNamespace(family=socket.AF_INET))):
            with self.assertRaises(ValueError): common.activated_listener()

    def test_examples_keep_processes_disjoint_secretless_ingress_and_no_queue(self):
        ingress_unit = (CONTACT / 'contact-ingress.service').read_text()
        relay_unit = (CONTACT / 'contact-relay.service').read_text()
        self.assertIn('User=contact-ingress\n', ingress_unit)
        self.assertIn('User=contact-relay\n', relay_unit)
        self.assertIn('RestrictAddressFamilies=AF_UNIX\n', ingress_unit)
        self.assertIn('PrivateNetwork=yes\n', ingress_unit)
        self.assertIn('IPAddressDeny=any\n', ingress_unit)
        self.assertNotIn('LoadCredential', ingress_unit)
        self.assertIn('LoadCredentialEncrypted=smtp-password:', relay_unit)
        self.assertIn('IPAddressDeny=any\n', relay_unit)
        self.assertEqual(['IPAddressAllow='], [line for line in relay_unit.splitlines()
                                            if line.startswith('IPAddressAllow=')])
        for unit in (ingress_unit, relay_unit):
            self.assertIn('StandardOutput=null\n', unit); self.assertIn('StandardError=null\n', unit)
            self.assertIn('ProtectSystem=strict\n', unit)
            self.assertNotIn('StateDirectory=', unit)
        proxy = (CONTACT / 'nginx.example.conf').read_text()
        for setting in ('proxy_pass_request_headers off;', 'proxy_request_buffering off;',
                        'proxy_next_upstream off;', 'access_log off;', 'client_body_buffer_size 64k;'):
            self.assertIn(setting, proxy)
        self.assertNotIn('X-Forwarded', proxy)
        for code, name, path in ((413, 'invalid', 'invalid'), (429, 'rate-limited', 'rate-limited')):
            self.assertIn(f'error_page {code} = @contact-{name};', proxy)
            self.assertIn(f'location @contact-{name} {{ return 303 /contact/{path}/; }}', proxy)
        self.assertIn('error_page 502 503 504 = @contact-unavailable;', proxy)
        self.assertIn('location @contact-unavailable { return 303 /contact/unavailable/; }', proxy)
        self.assertNotIn('=303', proxy)
        self.assertEqual('smtp.example.invalid', CONFIG['smtp_host'])


class SMTPSink:
    def __init__(self, certificate, key, mode, *, reject=None):
        self.tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.tls.load_cert_chain(certificate, key)
        self.mode = mode
        self.reject = reject
        self.commands = []
        self.messages = []
        self.tls_used = False
        self.server = LocalServer(socket.AF_INET, ('127.0.0.1', 0), self.handle)

    def handle(self, connection):
        connection.settimeout(2)
        stream = None
        try:
            if self.mode == 'ssl':
                connection = self.tls.wrap_socket(connection, server_side=True)
                self.tls_used = True
            stream = connection.makefile('rb')
            connection.sendall(b'220 synthetic.invalid\r\n')
            while True:
                line = stream.readline(4096)
                if not line:
                    break
                command = line.split(b' ', 1)[0].strip().upper()
                self.commands.append(command)
                if command == b'EHLO':
                    if self.mode == 'starttls' and not self.tls_used:
                        connection.sendall(b'250-synthetic.invalid\r\n250 STARTTLS\r\n')
                    else:
                        connection.sendall(b'250-synthetic.invalid\r\n250 AUTH PLAIN\r\n')
                elif command == b'STARTTLS':
                    connection.sendall(b'220 start encryption\r\n'); stream.close()
                    connection = self.tls.wrap_socket(connection, server_side=True)
                    self.tls_used = True; stream = connection.makefile('rb')
                elif command == b'AUTH':
                    # Fake account only. Never store the AUTH payload.
                    connection.sendall(b'535 refused\r\n' if self.reject == 'auth' else b'235 authenticated\r\n')
                elif command in (b'MAIL', b'RCPT'):
                    self.commands[-1] = line.strip()
                    connection.sendall(b'550 refused\r\n' if self.reject == command.decode().lower() else b'250 accepted\r\n')
                elif command == b'DATA':
                    connection.sendall(b'354 send data\r\n')
                    body = bytearray()
                    while True:
                        part = stream.readline(4096)
                        if not part: raise OSError()
                        if part == b'.\r\n': break
                        if part.startswith(b'..'): part = part[1:]
                        body.extend(part)
                        if len(body) > 65536: raise OSError()
                    if self.reject == 'disconnect': break
                    connection.sendall(b'554 refused\r\n' if self.reject == 'data' else b'250 queued\r\n')
                    if self.reject != 'data': self.messages.append(bytes(body))
                elif command == b'RSET':
                    connection.sendall(b'250 reset\r\n')
                else:
                    connection.sendall(b'500 unsupported\r\n')
        except (OSError, ssl.SSLError):
            pass
        finally:
            if stream is not None: stream.close()
            connection.close()

    def __enter__(self):
        self.server.__enter__()
        return self

    def __exit__(self, *args):
        return self.server.__exit__(*args)

    def config(self):
        # Ephemeral test ports are constructed in memory. Public config parsing
        # separately proves only the production TLS/port pairs are admitted.
        return dict(CONFIG, smtp_host='127.0.0.1', smtp_port=self.server.address[1], tls=self.mode)


class SMTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory(prefix='contact-tls-')
        cls.certificate = str(Path(cls.directory.name) / 'cert.pem')
        cls.key = str(Path(cls.directory.name) / 'key.pem')
        try:
            result = subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes',
                '-keyout', cls.key, '-out', cls.certificate, '-days', '1', '-subj', '/CN=synthetic.invalid',
                '-addext', 'subjectAltName=IP:127.0.0.1,DNS:synthetic.invalid', '-addext', 'basicConstraints=critical,CA:TRUE',
                '-addext', 'keyUsage=critical,keyCertSign,digitalSignature,keyEncipherment',
                '-addext', 'extendedKeyUsage=serverAuth'], capture_output=True, timeout=15)
            if result.returncode: raise AssertionError('synthetic TLS fixture unavailable')
        except BaseException:
            cls.directory.cleanup()
            raise

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def trusted(self):
        return ssl.create_default_context(cafile=self.certificate)

    def test_native_resolver_stall_is_reaped_and_next_submission_succeeds(self):
        # A native C call defers Python's signal handler. The independent
        # subprocess deadline must still terminate it and free the serial relay.
        children = []
        popen = subprocess.Popen
        def record(*args, **kwargs):
            child = popen(*args, **kwargs)
            children.append(child)
            return child
        with tempfile.TemporaryDirectory(prefix='contact-resolver-') as directory:
            path = str(Path(directory) / 'relay.sock')
            ready = Path(directory) / 'native-call-started'
            stalled = '''import ctypes,pathlib,signal
libc=ctypes.CDLL(None)
signal.signal(signal.SIGALRM,lambda *_: None)
signal.setitimer(signal.ITIMER_REAL,0.05)
pathlib.Path(READY).write_text('ready')
while True: libc.sleep(30)
'''.replace('READY', repr(str(ready)))
            with SMTPSink(self.certificate, self.key, 'ssl') as sink:
                app = relay.Relay(1234, sink.config(), PASSWORD)
                deliver = relay.deliver
                def trusted(config, password, value):
                    return deliver(config, password, value, context=self.trusted())
                with (patch.object(relay, 'peer_uid', return_value=1234),
                      patch.object(relay, 'deliver', side_effect=trusted),
                      patch.object(relay.subprocess, 'Popen', side_effect=record),
                      LocalServer(socket.AF_UNIX, path, app.handle)):
                    with patch.object(relay, 'RESOLVER_SOURCE', stalled), patch.object(relay, 'RESOLVE_TIMEOUT', 1):
                        started = time.monotonic()
                        self.assertEqual(b'UNAVAILABLE\n', common.relay_call(path, VALUE))
                        self.assertLess(time.monotonic() - started, 3)
                    self.assertEqual('ready', ready.read_text())
                    self.assertEqual(b'SENT\n', common.relay_call(path, VALUE),
                                     msg=[child.returncode for child in children])
            self.assertEqual(1, len(sink.messages))
        self.assertEqual(2, len(children))
        self.assertLess(children[0].returncode, 0)
        self.assertEqual(0, children[1].returncode)
        self.assertTrue(all(child.poll() is not None for child in children))

    def test_tls_checks_configured_hostname_without_a_second_resolution(self):
        for host, expected in (('synthetic.invalid', b'SENT\n'), ('other.invalid', b'UNAVAILABLE\n')):
            with SMTPSink(self.certificate, self.key, 'ssl') as sink:
                config = dict(sink.config(), smtp_host=host)
                with (patch.object(relay, 'resolve_addresses', return_value=[[4, '127.0.0.1', 0]]),
                      patch.object(socket, 'getaddrinfo', side_effect=AssertionError('second lookup'))):
                    self.assertEqual(expected, relay.deliver(config, PASSWORD, VALUE, context=self.trusted()))
            self.assertEqual(1 if expected == b'SENT\n' else 0, len(sink.messages))
            if expected != b'SENT\n':
                self.assertFalse(any(command == b'AUTH' for command in sink.commands))

    def test_real_ssl_and_starttls_sink_accept_only_fixed_envelope_and_reply_to(self):
        cases = [('ssl', CONFIG['mail_from'], CONFIG['mail_to']),
                 ('starttls', CONFIG['mail_from'], CONFIG['mail_to']),
                 ('ssl', 'Form.Tag@Example.Invalid', 'Inbox+Case@Example.Invalid')]
        for mode, sender, recipient in cases:
            with self.subTest(mode=mode, mixed_case=sender != CONFIG['mail_from']), SMTPSink(self.certificate, self.key, mode) as sink:
                config = dict(sink.config(), mail_from=sender, mail_to=recipient)
                self.assertEqual(b'SENT\n', relay.deliver(config, PASSWORD, VALUE, context=self.trusted()))
            self.assertTrue(sink.tls_used)
            self.assertEqual(1, len(sink.messages))
            # SMTP keywords ignore case. Keep everything after the colon so
            # mailbox local-part and domain bytes are compared exactly.
            envelopes = [(prefix.upper(), address) for command in sink.commands
                         for prefix, colon, address in [command.partition(b':')] if colon]
            self.assertEqual([(b'MAIL FROM', ('<' + sender + '>').encode('ascii')),
                              (b'RCPT TO', ('<' + recipient + '>').encode('ascii'))], envelopes)
            self.assertFalse(any(VALUE['email'].encode() in c for c in sink.commands))
            self.assertEqual([b'AUTH'], [c for c in sink.commands if c.split(b' ', 1)[0].upper() == b'AUTH'])
            self.assertNotIn(PASSWORD.encode(), b'\n'.join(sink.commands) + sink.messages[0])
            message = BytesParser(policy=policy.default).parsebytes(sink.messages[0])
            self.assertEqual(sender, message['From']); self.assertEqual(recipient, message['To'])
            self.assertEqual(CONFIG['subject'], message['Subject'])
            self.assertEqual(VALUE['email'], message['Reply-To'])
            self.assertEqual(VALUE['message'], message.get_content().strip())
            self.assertIsNone(message['Bcc']); self.assertIsNone(message['Cc'])
            self.assertTrue(sink.messages[0].isascii())
            if mode == 'starttls':
                self.assertLess(sink.commands.index(b'STARTTLS'), sink.commands.index(b'AUTH'))
                self.assertEqual(2, sink.commands.count(b'EHLO'))

    def test_certificate_trust_and_hostname_failure_send_no_auth_or_message(self):
        for wrong_host in (False, True):
            with SMTPSink(self.certificate, self.key, 'ssl') as sink:
                config = sink.config()
                if wrong_host: config['smtp_host'] = 'localhost'
                result = relay.deliver(config, PASSWORD, VALUE,
                    context=self.trusted() if wrong_host else ssl.create_default_context())
                self.assertEqual(b'UNAVAILABLE\n', result)
            self.assertNotIn(b'AUTH', sink.commands); self.assertEqual([], sink.messages)

    def test_missing_starttls_has_no_plaintext_auth_or_delivery(self):
        with SMTPSink(self.certificate, self.key, 'no_starttls') as sink:
            config = dict(sink.config(), tls='starttls')
            self.assertEqual(b'UNAVAILABLE\n', relay.deliver(config, PASSWORD, VALUE, context=self.trusted()))
        self.assertNotIn(b'AUTH', sink.commands); self.assertEqual([], sink.messages)

    def test_auth_sender_recipient_data_and_disconnect_never_report_success(self):
        for refusal in ('auth', 'mail', 'rcpt', 'data', 'disconnect'):
            with self.subTest(refusal=refusal), SMTPSink(self.certificate, self.key, 'ssl', reject=refusal) as sink:
                self.assertEqual(b'UNAVAILABLE\n', relay.deliver(sink.config(), PASSWORD, VALUE, context=self.trusted()))
            self.assertEqual([], sink.messages)

    def test_unix_http_to_relay_to_tls_sink_has_no_pii_output(self):
        output = io.StringIO()
        with tempfile.TemporaryDirectory(prefix='contact-chain-') as directory:
            relay_path = str(Path(directory) / 'relay.sock'); http_path = str(Path(directory) / 'http.sock')
            with SMTPSink(self.certificate, self.key, 'ssl') as sink:
                app = relay.Relay(1234, sink.config(), PASSWORD)
                actual_deliver = relay.deliver
                def trusted_delivery(config, password, value):
                    return actual_deliver(config, password, value, context=self.trusted())
                # macOS has no stdlib SO_PEERCRED. Only the identity syscall is
                # substituted here. Framing, HTTP, TLS, AUTH and DATA are real.
                with (patch.object(relay, 'peer_uid', return_value=1234),
                      patch.object(relay, 'deliver', side_effect=trusted_delivery),
                      contextlib.redirect_stdout(output), contextlib.redirect_stderr(output),
                      LocalServer(socket.AF_UNIX, relay_path, app.handle),
                      LocalServer(socket.AF_UNIX, http_path, ingress.Ingress(relay_path).handle)):
                    response = exchange(socket.AF_UNIX, http_path, request())
            self.assertIn(b'Location: /contact/sent/', response)
            self.assertEqual(1, len(sink.messages)); self.assertEqual('', output.getvalue())
        self.assertFalse(Path(directory).exists())

    def test_actual_smtp_data_refusal_propagates_to_http_unavailable(self):
        with tempfile.TemporaryDirectory(prefix='contact-refused-') as directory:
            relay_path = str(Path(directory) / 'relay.sock'); http_path = str(Path(directory) / 'http.sock')
            with SMTPSink(self.certificate, self.key, 'starttls', reject='data') as sink:
                app = relay.Relay(1234, sink.config(), PASSWORD)
                actual_deliver = relay.deliver
                def trusted_delivery(config, password, value):
                    return actual_deliver(config, password, value, context=self.trusted())
                with (patch.object(relay, 'peer_uid', return_value=1234),
                      patch.object(relay, 'deliver', side_effect=trusted_delivery),
                      LocalServer(socket.AF_UNIX, relay_path, app.handle),
                      LocalServer(socket.AF_UNIX, http_path, ingress.Ingress(relay_path).handle)):
                    response = exchange(socket.AF_UNIX, http_path, request())
            self.assertIn(b'Location: /contact/unavailable/', response)
            self.assertNotIn(b'/contact/sent/', response)
            self.assertEqual([], sink.messages)

    def test_multiline_text_is_plain_body_through_real_http_unix_and_tls(self):
        text = ('Hello ' + chr(0xe9) + '\r\n\r\n\tIndented text\r\n'
                'Bcc: other@example.invalid\nSubject: body text only\nThanks')
        value = dict(VALUE, message=text)
        with tempfile.TemporaryDirectory(prefix='contact-multiline-') as directory:
            relay_path = str(Path(directory) / 'relay.sock'); http_path = str(Path(directory) / 'http.sock')
            with SMTPSink(self.certificate, self.key, 'starttls') as sink:
                app = relay.Relay(1234, sink.config(), PASSWORD)
                actual_deliver = relay.deliver
                def trusted_delivery(config, password, submitted):
                    return actual_deliver(config, password, submitted, context=self.trusted())
                with (patch.object(relay, 'peer_uid', return_value=1234),
                      patch.object(relay, 'deliver', side_effect=trusted_delivery),
                      LocalServer(socket.AF_UNIX, relay_path, app.handle),
                      LocalServer(socket.AF_UNIX, http_path, ingress.Ingress(relay_path).handle)):
                    response = exchange(socket.AF_UNIX, http_path, request(urlencode(value).encode()))
            self.assertIn(b'Location: /contact/sent/', response)
            self.assertTrue(sink.tls_used)
            self.assertEqual(1, len(sink.messages))
            message = BytesParser(policy=policy.default).parsebytes(sink.messages[0])
            self.assertEqual(text.replace('\r\n', '\n') + '\n',
                             message.get_content().replace('\r\n', '\n'))
            for field, expected in (('From', CONFIG['mail_from']), ('To', CONFIG['mail_to']),
                                    ('Subject', CONFIG['subject']), ('Reply-To', VALUE['email'])):
                self.assertEqual([expected], message.get_all(field))
            self.assertIsNone(message['Bcc']); self.assertIsNone(message['Cc'])

    def test_maximum_unicode_message_survives_real_http_unix_and_smtp(self):
        value = dict(VALUE, message=chr(0x1f642) * 4000)
        with tempfile.TemporaryDirectory(prefix='contact-boundary-') as directory:
            relay_path = str(Path(directory) / 'relay.sock'); http_path = str(Path(directory) / 'http.sock')
            with SMTPSink(self.certificate, self.key, 'ssl') as sink:
                app = relay.Relay(1234, sink.config(), PASSWORD)
                actual_deliver = relay.deliver
                def trusted_delivery(config, password, submission):
                    return actual_deliver(config, password, submission, context=self.trusted())
                with (patch.object(relay, 'peer_uid', return_value=1234),
                      patch.object(relay, 'deliver', side_effect=trusted_delivery),
                      LocalServer(socket.AF_UNIX, relay_path, app.handle),
                      LocalServer(socket.AF_UNIX, http_path, ingress.Ingress(relay_path).handle)):
                    response = exchange(socket.AF_UNIX, http_path, request(urlencode(value).encode()))
            self.assertIn(b'Location: /contact/sent/', response)
            self.assertEqual(1, len(sink.messages))
            message = BytesParser(policy=policy.default).parsebytes(sink.messages[0])
            self.assertEqual(value['message'], message.get_content().strip())

    def test_unverified_tls_context_and_submission_injection_refuse_before_connection(self):
        context = ssl._create_unverified_context()
        with patch.object(relay.smtplib, 'SMTP_SSL') as connect:
            with self.assertRaises(ValueError): relay.deliver(CONFIG, PASSWORD, VALUE, context=context)
            with self.assertRaises(ValueError): relay.deliver(CONFIG, PASSWORD,
                dict(VALUE, email='a@example.invalid\r\nBcc: b@example.invalid'))
            connect.assert_not_called()


if __name__ == '__main__':
    unittest.main()
