---
title: "Legal"
description: "Impressum and privacy information for the DiamaneOS website and network services."
lede: "How the website and DiamaneOS network services handle data, and how to contact the controller."
---

## Impressum {#impressum}

Information under § 5 DDG.

Abhinav Jhanwar\
c/o RA Matutis\
Berliner Straße 57\
14467 Potsdam

Email: [hello@diamaneos.de](mailto:hello@diamaneos.de)

[Contact form](/about/#contact)

## Privacy policy {#privacy}

This notice covers this website, the web installer, the network services DiamaneOS phones use and contact by mail or the contact form. The attestation service has [its own notice](https://attestation.diamaneos.de/privacy-policy).

### Controller

The controller is the person named in the [Impressum](#impressum). Send privacy requests to the postal or email address there.

### Website

These pages set no cookies, run no scripts and store nothing on your device. Fonts, images and styles come from this site. There is no analytics, advertising or embedded third-party content. The contact form posts to this site's own handler.

Each request gives the server your IP address, the request time, the requested page and your browser's headers. The website runs on a server at OVHcloud in Germany.

Links to other websites are plain links. Following one connects your browser to that website, and its own privacy policy applies.

### Web installer

The [web installer](https://install.diamaneos.de) is static files on the same server, with the same request data and no cookies. Its scripts run in your browser, talk to the phone over USB and read any image set you choose on your computer. Its only other requests download a release from releases.diamaneos.de, and their path names the phone model.

### Phone services

DiamaneOS phones contact these services on their own, for example to check internet access, set the time or provision keys. Sending this information from the phone is strictly necessary for functions the phone provides to its user (Section 25(2) No. 2 TDDDG), so no consent is asked. Each connection can be changed or switched off on the phone, as the [FAQ](/faq/#default-connections) describes.

| Service | Data processed for the request |
| --- | --- |
| Connectivity and online checks | Connection metadata and HTTP headers. No account is needed. The checks also run over plain HTTP, so networks on the path can see them |
| Network time | Connection metadata needed to return the time |
| OS and app downloads | Connection metadata and the requested catalogue, package or release path, which shows the phone model, release channel and version, or the app package |
| Satellite assistance data | Connection metadata and a fixed assistance-data file |
| Certificate Transparency data | Connection metadata and public log lists. No browsing history is sent |
| SUPL positioning assistance | Native positioning messages, which can contain device identifiers and location information |
| Attestation-key and Widevine provisioning | Native provisioning messages and permitted query fields, which can contain device identifiers |
| Optional network location | Nearby Wi-Fi and cellular identifiers, which can reveal approximate location |

The satellite and Certificate Transparency services fetch public files from Qualcomm and Google themselves. No request from your phone is passed on.

Relays pass other requests on to fixed destinations:

- Attestation-key provisioning goes to Google: a request with keys unique to the phone, needed for hardware attestation.
- Widevine provisioning goes to Google: a device certificate request, sent only when an app plays protected video.
- SUPL goes to Google: the positioning messages of the phone's modem, which can include the current cell and device identifiers.
- Network location goes to Apple, only when you choose an Apple option, which is off by default: nearby Wi-Fi and cellular identifiers, with no account or phone identifier.

The relays remove cookies and the headers that carry your IP address, so Google and Apple see the relay's address instead of yours. Other headers, such as the user agent, which can name the phone model and Android version, are passed on. The relays decrypt the requests and can process their contents in memory. They do not remove identifiers inside a native message or make it anonymous. They keep no cache or history of these requests.

DNS checks use the resolver selected on the phone and the authoritative DNS of INWX. Those providers can receive DNS queries. An OpenStreetMap geocoding service, when selected, is contacted directly, without a DiamaneOS relay. It receives the phone's IP address and the lookup text or coordinates.

Vanadium, the bundled browser, is GrapheneOS's signed build. It fetches its components from GrapheneOS's servers, and GrapheneOS's privacy policy applies to those requests. Apps, mobile carriers, eSIM providers and separately chosen DNS or location providers handle data under their own policies.

You do not have to provide this data. Without these connections some phone functions do not work.

### Contact

If you write to hello@diamaneos.de or use the contact form, your email address, your message and any attachments are processed to answer you. Providing a valid reply address is needed to get an answer. Do not include passwords, private keys or device identifiers you do not need to send.

The form accepts an email address and a plain-text message, without attachments. Its handler processes the message in memory and forwards it over encrypted mail transport. It keeps no message queue or request log, and request limits use temporary state. This is not end-to-end encryption: the mail service processes the message and its delivery metadata. The form sends no copy to the address you enter.

### Purposes and legal bases

- **Delivering pages and services, and limiting abuse:** Article 6(1)(f) GDPR. The legitimate interest is secure and reliable services, with request logging disabled.
- **Provisioning and positioning messages:** Article 6(1)(f) GDPR. The legitimate interest is providing the device functions these messages serve, with fixed destinations, bounded messages and no stored request contents.
- **Answering enquiries and follow-up:** Article 6(1)(f) GDPR. The legitimate interest is responding to people who contact the project.
- **Network location through Apple:** your consent, Article 6(1)(a) GDPR, given by choosing an Apple option on the phone. You can withdraw it at any time by choosing another option. This does not affect earlier requests.

The data is not used for advertising or profiling. There is no automated decision-making, including profiling (Article 22 GDPR).

### Hosting and recipients

| Services | Hosting provider | Server location |
| --- | :---: | :---: |
| Website, web installer, primary downloads, connectivity checks, time and service relays | [OVHcloud](https://www.ovhcloud.com/de/terms-and-conditions/privacy-policy/) | Germany |
| Optional OS and app download mirror, service status page | ServaRICA | Canada |
| Staging copies of the website, the web installer and downloads | netcup | Germany |
| Attestation | [OVHcloud](https://www.ovhcloud.com/de/terms-and-conditions/privacy-policy/) | France |

- Mail to hello@diamaneos.de and contact form messages are received and stored by [mailbox.org](https://mailbox.org/en/data-protection/) in Germany. Service notifications are also sent through it.
- Postal correspondence at the c/o address is handled by RA Matutis in Germany.
- Google and Apple process relayed requests as independent controllers under their own policies: [Google's privacy policy and frameworks](https://policies.google.com/privacy/frameworks?hl=en) and [Apple's privacy policy](https://www.apple.com/legal/privacy/en-ww/).
- Hosting and network providers can observe connections and keep their own security, account or billing records. Disabling request logs does not stop that.

### Transfers outside the EU

- **Canada:** the download mirror is run by Rica Web Services Inc. (ServaRICA). Canada's [adequacy decision](https://commission.europa.eu/law/law-topic/data-protection/international-dimension-data-protection/adequacy-decisions_en) covers commercial organisations subject to PIPEDA. A download from Canada exposes connection metadata to the Canadian host. Content signatures protect authenticity, not the confidentiality of that metadata.
- **USA, Google:** provisioning and SUPL requests go to Google LLC. Google is certified under the EU-U.S. Data Privacy Framework, for which the European Commission decided an adequate level of protection (Decision (EU) 2023/1795).
- **USA, Apple:** network-location requests reach Apple Inc. only after your explicit choice (Article 49(1)(a) GDPR). Apple relies on Standard Contractual Clauses, not the Data Privacy Framework, and DiamaneOS has no contract with Apple. US authorities may be able to access data held by Apple without the protections EU law requires.

### Retention

- **Requests:** the web servers keep no access logs and no request-related error logs. Rate limits keep addresses only in memory, until their limit state expires or the service restarts.
- **Operational logs:** kept in memory for at most one day and cleared on reboot. They describe how the services run, not who used them. Monitoring notices name a service and a failure or recovery category, without request contents or device identifiers.
- **Caches:** public assistance data, Certificate Transparency data and signed download files can be cached, without a history of requests.
- **Correspondence:** kept while the enquiry and its follow-up are active. Resolved conversations are reviewed quarterly and deleted from active mailboxes within six months of resolution. A legal obligation (Article 6(1)(c) GDPR) or a legal claim can require longer retention. mailbox.org states that it keeps daily mail backups for up to seven days.

### Attestation

When you use remote attestation, the service processes account, device and security-state information to verify device integrity and send selected alerts. Its separate [privacy policy](https://attestation.diamaneos.de/privacy-policy) explains that data, hosting, cookies and retention.

### Your rights

Under the [GDPR](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng), you can ask for access to your data and for its correction, erasure or restriction, where the legal conditions are met. You can also ask for portability where that right applies. Apart from correspondence, the services keep no request history that could be linked to you.

**Right to object.** Where processing relies on Article 6(1)(f) GDPR, you can object to it at any time for reasons arising from your particular situation (Article 21 GDPR). Send the objection to the contact details in the [Impressum](#impressum). To stop your phone's requests to a service, switch it off on the phone, as the [FAQ](/faq/#default-connections) describes.

You can complain to a data-protection supervisory authority, for example where you live or work.

Privacy requests are answered within one month. Where complexity or the number of requests needs it, this can be extended by up to two months. You are told the reason within the first month.
