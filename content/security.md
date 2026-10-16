---
title: "Security"
description: "How to report a security problem in DiamaneOS."
lede: "How to report a security problem."
---

## Report a vulnerability

Send confidential vulnerability reports to [security@diamaneos.de](mailto:security@diamaneos.de). Include the affected component, steps to reproduce the problem and its security impact.

Encrypt sensitive details with the [OpenPGP public key](/security-public.asc). Check its primary fingerprint before sending:

```text
4AB9 1DBA 4726 2048 497B A046 A6D9 A7C6 48A6 884E
```

The key is also available in [binary format](/security-public.pgp). The [fingerprint file](/security-fingerprints.txt) lists the primary key, signing subkey and encryption subkey, in that order.

Use the [issue tracker](https://github.com/DiamaneOS/issue-tracker/issues) for bugs that do not require confidentiality.

## Security contact

The [signed security.txt](/.well-known/security.txt) gives the reporting address and public key URL.

## Known limitations

The [known limitations](/limitations/) say where the supported devices are weaker.
