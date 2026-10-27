---
title: "Frequently asked questions"
description: "Answers to common questions about DiamaneOS, installation, updates and privacy."
lede: "Installation, updates and privacy questions."
---

{{< page-index >}}

## Which phones are supported? {#device-support}

The [supported devices](/devices/) page lists the phones DiamaneOS runs on. Check it before installing. Similar model names do not imply compatible firmware or partitions.

## Why am I seeing a message about my bootloader not being locked during setup? {#bootloader-locking-setup}

The bootloader is still unlocked. Lock it before you continue: only a locked bootloader enforces verified boot, which stops a modified operating system from starting.

In the setup wizard, choose **Reboot to bootloader**, connect the phone to your computer and follow the [locking steps of the command-line guide](/install/cli/#locking-the-bootloader). They first check whether locking is safe. The [web installer](/install/web/#locking-the-bootloader) locks only straight after its own install, so install again with it and lock right away.

Locking erases the phone, as unlocking does, and setup starts again.

## Does a user build mean it is a signed release? {#user-builds}

No. The `user` variant turns root debugging off. It does not decide how a build is signed, and a build flag or file name cannot prove who signed it. The [build guide](/build/) explains the difference.

## Can my source build receive project updates? {#source-build-updates}

No. A source build has no Updater, and it accepts only updates signed with the keys it was built with, Android's public test keys or your own. DiamaneOS's updates are signed with the project's key, so your build cannot install them. Install your next build over it, as the [build guide](/build/#updates-that-keep-data) describes. To switch to DiamaneOS's factory images, follow the [install guide](/install/), which erases the phone.

## Where are the release notes for apps? {#app-release-notes}

Apps the App Store takes from GrapheneOS's catalog come unchanged from GrapheneOS, through DiamaneOS's download servers. GrapheneOS's own apps publish their release notes as GitHub releases in [GrapheneOS's repositories](https://github.com/GrapheneOS).

DiamaneOS's own [Camera](https://github.com/DiamaneOS/Camera), [App Store](https://github.com/DiamaneOS/AppStore) and [Auditor](https://github.com/DiamaneOS/Auditor) record their changes in each repository's commit history. Their version tags are signed and named after the version code, such as `9307` for Camera.

## What can the servers see? {#server-privacy}

The host handling a request can see connection metadata, including your IP address and requested file or service. A VPN substitutes its exit address. DiamaneOS disables request logs. Providers have their own visibility and policies. See the [privacy policy](/legal/#privacy).

## What does the phone connect to by default? {#default-connections}

Each goes to a DiamaneOS server and can be changed or switched off. Some exist only on devices whose hardware uses them, and Settings shows a choice only where it applies:

- Internet connectivity checks and Certificate Transparency downloads: Settings > Network & internet.
- Attestation key provisioning and Widevine provisioning, on devices whose secure hardware uses them: Settings > Network & internet. Widevine only connects when an app plays protected video.
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

The choice works whether eSIM support is on or off. Settings > System > Reset options > Erase eSIMs erases them without a factory reset.

The box appears once an eSIM has been added since DiamaneOS was last installed. Otherwise turn on developer options by tapping **Build number** seven times under Settings > About phone. The box then appears, and it erases every eSIM on the phone.

A duress PIN or password always erases every eSIM, also while eSIM support is off.

## Why do Bluetooth and Wi-Fi stay on in airplane mode? {#airplane-mode}

Airplane mode turns off the mobile network, Bluetooth and Wi-Fi. If you turn Bluetooth or Wi-Fi back on while airplane mode is on, the phone remembers that and leaves it on the next time you turn on airplane mode.

Bluetooth also stays on while headphones or another media device are connected.

To have airplane mode turn them off again, turn on airplane mode and then turn off Bluetooth or Wi-Fi. The phone remembers that too.

## Why did my phone restart by itself? {#auto-reboot}

Auto reboot restarts the phone when it has not been unlocked for 12 hours. The restart puts your data back at rest, encrypted with keys that only your PIN, password or passphrase unlocks. Until the next unlock, the data is far harder to get at, even with an exploit.

Alarms still ring after a restart, but apps and messages wait for the unlock. To change the time or turn auto reboot off, go to Settings > Security & privacy > Exploit protection > Auto reboot.

## Why does Bluetooth turn off by itself? {#bluetooth-auto-off}

Bluetooth turns off after 10 minutes without a connected device. Bluetooth that is off cannot be reached, and the chip's firmware gets fixes only from the device maker.

To change this, choose another time or **Never** under Settings > Security & privacy > Exploit protection > Turn off Bluetooth automatically.

## How do I use RCS? {#rcs}

RCS chats work in Google Messages with sandboxed Google Play, in the Owner user.

1. Install Google Play services from the App Store and Google Messages from the Play Store.
2. Make Google Messages the default SMS app.
3. Allow **Phone** for Google Play services under Settings > Apps > Google Play services > Permissions.
4. In Google Messages, turn on RCS under Settings > RCS chats.

Some networks check the SIM before RCS starts and stay on "Connecting" without it. For these, turn on **Allow ICC authentication with device identifiers** under Settings > Apps > Sandboxed Google Play > Play services special permissions. A notification points there when it is needed. Some carriers also need Google's Carrier Services app from the Play Store.

If RCS stayed on "Connecting" before these steps, clear Google Messages' storage and restart the phone, so it tries again.

## Where should problems be reported? {#reporting-problems}

Send sensitive security reports to [security@diamaneos.de](mailto:security@diamaneos.de). Use the [issue tracker](https://github.com/DiamaneOS/issue-tracker/issues) for ordinary bugs, and [hello@diamaneos.de](mailto:hello@diamaneos.de) or the [contact form](/about/#contact) for general questions. Keep account tokens, private keys and identifying diagnostic data out of public reports.
