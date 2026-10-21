---
title: "Known limitations"
description: "What does not work, or is not verified, on DiamaneOS."
lede: "What does not work, or is not verified, on the supported devices."
---

## Hardware and firmware

- **No secure element.** Limiting unlock guesses and holding keys rely on the phone's secure area (TEE), which is not verified.
- **A broken secure area leaves only the lock.** If the secure area were broken, only the strength of the lock would protect the data. A long random passphrase holds. A PIN you choose does not.
- **Wipes rely on the secure area.** A wipe asks the secure area to destroy the keys. That is no promise against someone who copied the storage first and later breaks the secure area.
- **Protected video at software level only.** DiamaneOS uses Widevine L3, the software level, for protected video. Streaming apps can limit its quality, often to standard definition.
- **No Play Integrity verdict.** Google's Play Integrity check gives DiamaneOS no verdict, not even basic integrity. Apps that require it, such as some banking and payment apps, refuse to work or limit features.
- **Auditor relies on its first pairing.** Every check is genuine hardware attestation from the phone's secure area. The device maker cannot vouch for the first pairing, so it is only as trustworthy as the phone was at that moment. After a reset, the phone must be paired again.
- **No memory tagging.** Memory bugs are easier to exploit than on phones that have it.
- **No virtual machines.** The phone's firmware would start protected virtual machines without the protection they rely on, so DiamaneOS leaves them off. Ordinary ones, such as a Linux terminal, are refused by that firmware.
- **Firmware fixes come from the device maker.** The bootloader, modem and other firmware are closed and come from the device maker and Qualcomm. DiamaneOS cannot fix them. Fixes arrive with the device maker's releases.

## Security

- **USB-C Off is not a full switch-off.** With the USB-C port set to Off, the phone exchanges no data and does not charge. A charger or other USB-C device can still detect the phone, because the charging chip's own firmware keeps that part on. The phone also charges for a few seconds each time it starts.
- **Flash mode by hardware keys.** Someone holding the phone can start Qualcomm's emergency download mode (EDL) with the keys. Using it needs a signed tool.
- **No head trackers.** Head trackers on paired Bluetooth and USB devices do not work, because their parser is not shipped.

## Camera

- **Night and Portrait photos are finished after the shot.** Taking the photo is instant. The camera app then processes it on the phone, and it appears in the gallery about 15 seconds later. You can keep taking photos meanwhile.

## Updates

- **Behind GrapheneOS.** DiamaneOS follows one GrapheneOS release at a time. The [source manifest](https://github.com/DiamaneOS/platform_manifest/tree/android17) names it.

## Mobile network

- **Emergency calls tested only in simulation.** No call to an emergency number has been made.
- **No microphone in emergency calls with the Moments switch down.** With the switch action Camera and microphone off, the kernel keeps the built-in microphones off during an emergency call too. Sliding the switch up turns them back on.
- **Wi-Fi calling needs a restart after a clean install.** On the first start, Wi-Fi calling and VoLTE can stay unavailable. The phone then offers a restart, which brings them up.
