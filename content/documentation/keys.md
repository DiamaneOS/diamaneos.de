---
title: "Public keys"
description: "The public keys and certificate digests to check DiamaneOS's factory images, phones, apps and attestation against."
lede: "Check factory images, phones and apps against DiamaneOS's keys."
---

## Verified boot key {#verified-boot-key}

The phone checks every OS image against this key. The install writes it to the phone, and each image set carries it as `avb_pkmd.bin`.

- Key files: [avb_pkmd.bin](/keys/avb_pkmd.bin), as the phone stores it, and [avb.pub.pem](/keys/avb.pub.pem) for `avbtool`.
- The key ID is the SHA-256 of `avb_pkmd.bin`:

```text
5c4c94ba54e9f4fe81dcfd77e9b919204f0a493593a2677b50498cbcb6cd8f8d
```

- A locked phone shows this ID on its yellow warning screen at each start. Another ID means it runs an OS signed with another key.
- In an unpacked image set, `sha256sum avb_pkmd.bin` must print it.
- Attestation reports the same value as the verified boot key.

## Factory images {#factory-images}

The factory images of each release are signed with an Ed25519 SSH key. The [allowed signers file](/keys/factory.allowed_signers) holds it:

```text
diamaneos ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIB+N9xKoysBkgXsI9di16Bamn6d2wIULS5SfJazATsZ0
```

- Its fingerprint is `SHA256:efhtysP+8Tz5vKgjZT6MEfiK3h3bH2/cjW3w3cg6How`.
- The install guide shows [how to check the factory images](/install/cli/#verifying-the-factory-images) with it.
- Source commits and tags have their own key, in the [build guide](/build/#verifying-the-source).

## Apps {#apps}

DiamaneOS signs its own builds of these apps. Check an app file with `apksigner verify --print-certs FILE.apk`. The certificate SHA-256 digest it prints must match.

App Store, `app.grapheneos.apps`:

```text
559ffb104edd9386a39d512063cb7458c5ec0e29c9b52a91068ce950dd768a47
```

Camera, `app.grapheneos.camera`:

```text
285a091a913f1485ce16f280f06b2609dc1af6cca786e45b6f5356aa7e86fa61
```

Camera processing, `de.diamaneos.camera.processor`, signed with the Camera's key:

```text
285a091a913f1485ce16f280f06b2609dc1af6cca786e45b6f5356aa7e86fa61
```

Auditor, `de.diamaneos.auditor`:

```text
427bfd360586b829475f37abffd2548d93db3618e45c994de416469ef04bc2ec
```

The App Store checks the app catalog it downloads against the signify key [apps.0.pub](/keys/apps.0.pub):

```text
RWRM77BKHPPXnI2+ijuXz5phnaGpVGZuK8R6GM7uX5Wonc/5YiLsiJF3
```

## Attestation release list {#attestation-release-list}

Where the device maker cannot vouch for the first pairing, Auditor pairs a phone only if it reports exactly the values of a DiamaneOS release from this signed list. A modified build cannot be paired.

- [release-list.pub.pem](/keys/release-list.pub.pem) is the list's P-256 signing key.
- Each signature in the list names it by `keyId`, the SHA-256 of the key in DER form:

```text
0B0A4D2CD3680FF4F3993CA8A61CDA93417680F5151090154EDCD52655C7E4AB
```
