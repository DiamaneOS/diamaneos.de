---
title: "Attestation explained"
description: "What Auditor verifies and what an attestation result can establish."
lede: "Check device identity and boot state against a trusted baseline."
---

This page explains the protocol. It is not a pairing or enrollment walkthrough. Device and OS support depend on the trust policy in the app and server source.

## What is attestation?

Auditor asks a device's hardware-backed security environment to produce evidence about its identity, boot state and software. The verifier checks that evidence against trusted roots, supported-device rules and expected OS identities. A report supplied by Android alone is not enough.

A trusted result depends on recognising the device and its signing identity. Installing Auditor on an unsupported OS does not add that OS to the verifier's trust policy. The [Auditor source](https://github.com/DiamaneOS/Auditor) and [server source](https://github.com/DiamaneOS/AttestationServer) define those checks.

## Local verification

Local verification uses two devices: the device being checked and an independent verifier. QR codes carry a fresh challenge and its signed response. Pairing creates a relationship that later checks can compare against, rather than treating every check as a new device.

The first check establishes a baseline. Later checks can detect changes to the paired identity and reported state. Keep the verifier under independent control. A compromised verifier cannot provide a trustworthy result.

## Remote verification

Remote verification uses a server as the independent verifier. An enrolled device sends scheduled attestations so the service can compare its identity and state over time. A missed check is a warning requiring investigation, not proof that the phone was compromised.

Remote verification has an account and device history. It is a separate service from OS updates and download-region selection. Its [privacy policy](https://attestation.diamaneos.de/privacy-policy) describes the retained account, device and verification records.

## Limits and failures

Attestation evaluates the supported security properties reported by the hardware and verified boot chain. It does not prove the absence of every malicious app, software vulnerability or compromised peripheral. Hardware and firmware limits still matter. See [known limitations](/limitations/).

On some phones the device maker cannot vouch for the first pairing. The person pairing then confirms that they trust how the phone was set up. Every later check is hardware attestation pinned to that first pairing. A factory reset erases Auditor's key, so the phone must be paired again.

An unsupported identity, changed pairing or invalid signature must fail rather than be silently trusted. Check the reported reason and the expected public identity. Do not erase pairing history merely to make an unexpected failure disappear.

If network checks stop arriving, investigate connectivity and service availability as well as the phone. Preserve the evidence before resetting either side. Report sensitive findings through [Security](/security/), without posting account tokens or private reports publicly.
