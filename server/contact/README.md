This backend receives same-origin contact submissions and forwards them through verified SMTP TLS. Its separate ingress has no SMTP credentials or IP egress. Neither process logs submissions or maintains a persistent queue. Global limits reduce volume but do not prevent every form of abuse.

Submit `POST /contact/submit` with Origin `https://diamaneos.de` and `application/x-www-form-urlencoded`. Exactly `email` and `message` are accepted. Email uses ASCII dot-atom addr-spec. The HTTP body limit is 64 KiB.

Messages accept LF/CRLF line breaks and tabs as plain body text. CRLF becomes LF. The normalized message limit is 4000 Unicode characters. Empty messages, other controls including NUL, and format characters are refused. Email and headers reject line breaks.

Every submission outcome redirects with 303 to `/contact/sent/`, `/contact/invalid/`, `/contact/unavailable/`, or `/contact/rate-limited/`. “Sent” means the configured upstream accepted SMTP DATA, not confirmed inbox delivery. No confirmation or bounce is addressed to the submitter. Their address appears only in Reply-To.

Install the three Python files read-only under `/opt/diamaneos-contact` on maintained Linux Python 3.11 or later. The supplied systemd socket/services and sysusers file are examples. Create separate non-root accounts. nginx reaches ingress, and ingress reaches relay. Both services consume one inherited Unix listener.

Replace `relay.example.json` with a protected role configuration at `/etc/diamaneos-contact/relay.json`. Supported pairs are `ssl`/465 and mandatory `starttls`/587. Sender, recipient, subject and SMTP host are configuration, never form fields. The examples use invented domains and do not enable delivery.

Relay defaults to `IPAddressDeny=any`. Add a root-controlled service drop-in with `IPAddressAllow=` only for exact SMTP destination addresses and exact resolver IPs when IP DNS is required. Do not allow whole loopback ranges or destination subnets.

Restrict destination ports and transport through the root-controlled egress firewall: configured TLS SMTP port and required resolver transport only. Unix resolver access needs no IP exception. Enforce effective address denial, including inherited slice rules, with Linux cgroup filtering or equivalent firewall rules.

Provision `smtp-password` only through relay's `LoadCredentialEncrypted`. Missing or unsafe credentials/configuration refuse startup. Protect installed code and configuration against service-account writes. Integrate `nginx.example.conf` into the existing HTTPS host and keep its security headers and real peer-IP limit. Request logging and disk body buffering must stay disabled.

Both workers are serial, with bounded socket backlog, frame sizes and whole-request deadlines. Ingress allows five attempts, replenished every twenty seconds. Relay permits three attempts, replenished every five minutes. Limits are memory-only and reset on restart. There is no retry queue.

An interrupted delivery may have reached upstream, so a retry can duplicate it. Global limits bound inbox volume but can also delay legitimate enquiries during an attack.

SMTP name resolution runs in a separate process with a three-second deadline. A timeout kills and reaps it. No message or SMTP credential is passed to it. Connections use validated numeric results while TLS authenticates the configured hostname.

Run the unit, Unix-socket and synthetic TLS SMTP tests from the repository root:

```sh
python3 -B -m unittest discover -s tests -p test_contact.py
```

Local checks require OpenSSL and use temporary certificates with loopback SMTP sinks. Deployment requires Linux peer credentials, separate service accounts, enforced systemd isolation, encrypted SMTP credentials and an HTTPS proxy. Disable request logs and configure the host journal for volatile storage.

References: [Python SMTP](https://docs.python.org/3/library/smtplib.html), [TLS verification](https://docs.python.org/3/library/ssl.html#ssl.create_default_context), [systemd credentials](https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html#LoadCredentialEncrypted=), [systemd IP filters](https://www.freedesktop.org/software/systemd/man/latest/systemd.resource-control.html#IPAddressAllow=), [nginx proxy](https://nginx.org/en/docs/http/ngx_http_proxy_module.html).
