---
title: "Servers and service boundaries"
description: "Where DiamaneOS services run and how their access is constrained."
lede: "Separate service roles, limited access and public configuration source."
---

## Service roles

| Role | Purpose | Provider | Location |
| --- | --- | :---: | :---: |
| Primary | Website, connectivity checks, time, service relays and downloads | OVHcloud | Germany |
| Download mirror | Second server for OS and app downloads, service status page | ServaRICA | Canada |
| Attestation | Auditor's remote verification service and application state | OVHcloud | France |
| Staging | Separate website and download test endpoints | Netcup | Germany |

The download mirror serves the same OS and app files. With the default Automatic setting, the Updater and the App Store pick the faster of the two servers and continue an interrupted download on the other. The download servers setting can also limit them to one server. The mirror does not replace connectivity checks, time or positioning services. Staging is for tests and is not a download region.

Authoritative DNS is provided by INWX. DiamaneOS does not operate its own authoritative nameserver network. The [privacy policy](/legal/#privacy) describes the providers and data involved in requests.

{{< service-boundaries >}}

## Host and service isolation

Hosts use Debian with separate service accounts. Public ingress and forwarding are denied unless explicitly allowed. Administration uses an authenticated WireGuard management tunnel. Direct public SSH and password SSH are disabled.

Systemd constrains service filesystems, capabilities, devices, memory and processes. Serving accounts cannot rewrite their code, configuration or public files. Network egress is restricted by service identity and destination. A failed policy refresh does not grant unrestricted access.

These controls reduce attack surface. A virtual server's firewall cannot prevent every attack against the provider's network, and separate accounts on one host are not separate kernels. A hosting provider remains inside the trust boundary for its virtual machines.

## Website and relays

The website serves static HTML and CSS with local fonts and images. It runs no analytics or third-party embeds, and only the web installer runs scripts. TLS protects browser connections, and content security policy limits what a page can load or submit.

The contact form has separate ingress and mail workers. Input size, methods and request rates are bounded. The mail worker has a fixed sender, destination and SMTP route. Contact text is not stored as a web-server submission history.

Connectivity checks return the response Android expects. Positioning and provisioning relays have fixed upstream destinations. They are not open proxies. Assistance-data caches contain shared responses rather than a history of individual users' requests.

Request access logs and request-associated error logs are disabled. Temporary abuse controls use memory. Operational logs have a short volatile retention policy. Providers can still observe connections and keep their own records. This setup does not make IP addresses anonymous.

## Downloads and attestation

Download servers serve static artifacts. Artifact authenticity depends on independent signature verification, rather than trusting the server that supplies a file. A valid signature does not conceal your IP address, requested file or download time from the host.

Attestation has a separate stateful service. Its database resides on encrypted storage with no plaintext fallback. Storage encryption protects locked state. It does not hide data from a running application or a compromised host while that state is unlocked.

## Staging and recovery

Staging uses separate publication roots and TLS material. It does not contain the production database or production signing keys. Its public preview is excluded from crawlers. Crawler rules are not access control.

Source configuration can recreate services, but it cannot recreate database history or host secrets. A usable recovery also needs authenticated encrypted backups, independent keys and a restore test. Encrypted copies of server state go to Backblaze B2 every week, and restoring them is tested. Replicas and source repositories alone are not backups of application state.

## Configuration source

- [Infrastructure](https://github.com/DiamaneOS/infrastructure) contains the Debian host and service adapters.
- [Network services](https://github.com/DiamaneOS/network-services) contains the GrapheneOS-derived connectivity and relay configuration.
- [Release serving](https://github.com/DiamaneOS/releases.diamaneos.de) and [Apps serving](https://github.com/DiamaneOS/apps.diamaneos.de) contain download configuration.
- [AttestationServer](https://github.com/DiamaneOS/AttestationServer) contains the remote verification service.
- [Website](https://github.com/DiamaneOS/diamaneos.de) contains these pages and the contact handler.

DiamaneOS adapts GrapheneOS's public service code and configuration. GrapheneOS has not reviewed the Debian adapters, the DiamaneOS changes or this deployment.
