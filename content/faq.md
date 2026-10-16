---
title: "Frequently asked questions"
description: "Answers to common questions about DiamaneOS, installation, updates and privacy."
lede: "Installation, updates and privacy questions."
---

{{< page-index >}}

## Which phones are supported? {#device-support}

The [supported devices](/devices/) page lists the phones DiamaneOS runs on. Check it before installing. Similar model names do not imply compatible firmware or partitions.

## Why am I seeing a message about my bootloader not being locked during setup? {#bootloader-locking-setup}

After installing DiamaneOS's factory images, this warning means the bootloader was not locked. Lock it before continuing setup: a locked bootloader enforces verified boot with the operating system's key.

Open the [locking section of the install guide](/install/#locking-the-bootloader) on your computer. In the setup wizard, choose **Reboot to bootloader**, connect the phone by USB and follow those steps. They start with a check that tells you whether locking is safe.

Locking erases the phone, as unlocking does, and setup starts again. This keeps someone who changes the lock state from reaching your data.

A build you made yourself with the [build guide](/build/) must stay unlocked. Continue setup without locking.

## Does a user build mean it is a signed release? {#user-builds}

No. The `user` variant turns root debugging off. It does not decide how a build is signed, and a build flag or file name cannot prove who signed it. The [build guide](/build/) explains the difference.

## Can my source build receive project updates? {#source-build-updates}

No. A source build is signed with Android's public test keys and has no Updater, so it cannot install DiamaneOS's updates. Install your next build over it, as the [build guide](/build/#updates-that-keep-data) describes. To switch to DiamaneOS's factory images, follow the [install guide](/install/), which erases the phone.

## What can the servers see? {#server-privacy}

The host handling a request can see connection metadata, including your IP address and requested file or service. A VPN substitutes its exit address. DiamaneOS disables request logs. Providers have their own visibility and policies. See the [privacy policy](/legal/#privacy).

## What does the phone connect to by default? {#default-connections}

Each goes to a DiamaneOS server and can be changed or switched off:

- Internet connectivity checks, attestation key provisioning, Certificate Transparency downloads and Widevine provisioning: Settings > Network & internet. Widevine only connects when an app plays protected video.
- Satellite data (PSDS): Settings > Location.
- Network time: Settings > System > Date & time > Set time automatically.
- Network location is off by default: Settings > Location > Location services.

System and app updates check DiamaneOS's download servers.

## Which other connections can the phone make? {#other-connections}

SUPL speeds up a location fix with data from the mobile network's area. The phone's modem sends it through a DiamaneOS relay to Google. Change it or switch it off under Settings > Location.

Calls, SMS and mobile data go through your carrier. Adding an eSIM contacts the carrier's eSIM server. The Vanadium browser fetches its components from GrapheneOS.

## Does attestation prove the phone has no malware? {#attestation-limits}

No. It checks supported hardware-backed identity and boot-state properties against a trusted baseline. It does not prove the absence of every malicious app or vulnerability. A valid result also depends on the verifier and expected OS identity. See [attestation explained](/documentation/attestation/).

## Why publish advertising opt-out files if the site has no ads? {#advertising-opt-out}

Someone could falsely claim to sell advertising for our domain or apps. Our [ads.txt](/ads.txt) and [app-ads.txt](/app-ads.txt) declare that no seller is authorised. Advertising systems that check these files can reject that falsely labelled inventory.

These files do not block ads in your browser. GrapheneOS's [sitewide advertising industry opt-out article](https://grapheneos.org/articles/sitewide-advertising-industry-opt-out) explains the purpose and limits of the standard.

## Is a microSD card encrypted? {#microsd}

A card that a computer or camera already formatted (FAT32 or exFAT) works straight away as portable storage. Use it as it is and skip the setup the phone offers.

The setup asks how to use the card. Both of its choices erase the card.

**Format SD card for portable storage.** The card works like a USB drive. A computer, a camera or another phone can read it. It is not encrypted, so anyone who has the card can read it. This is the same on every Android phone, and USB drives always work this way.

**Format SD card for internal storage.** The card is encrypted and works only in this phone. Apps and their data stay on the phone's own storage. After formatting, the phone offers to move photos, downloads and other files to the card.

The card's key exists only on this phone. Choosing **Forget** for the card, or losing the phone, makes the card unreadable for good. Keep a copy of important files elsewhere.

## Does a factory reset erase eSIMs? {#esim-reset}

Only when you choose it. In Settings > System > Reset options > Erase all data (factory reset), tick **Erase eSIMs**.

The choice needs eSIM support, which is off by default. Turn it on under Settings > Network & internet. While eSIM support is off, the choice is greyed out and eSIMs stay on the phone.

The box appears once an eSIM has been added since DiamaneOS was last installed. Otherwise turn on developer options by tapping **Build number** seven times under Settings > About phone. The box then appears, and it erases every eSIM on the phone.

A duress PIN or password always erases every eSIM, even one added before DiamaneOS was installed and even while eSIM support is off.

## Where should problems be reported? {#reporting-problems}

Send sensitive security reports to [security@diamaneos.de](mailto:security@diamaneos.de). Use the [issue tracker](https://github.com/DiamaneOS/issue-tracker/issues) for ordinary bugs, and [hello@diamaneos.de](mailto:hello@diamaneos.de) or the [contact form](/about/#contact) for general questions. Keep account tokens, private keys and identifying diagnostic data out of public reports.
