---
title: "How releases are signed"
description: "Where the release keys live, what each one signs, and why a download server cannot forge or roll back an update."
lede: "The keys stay offline. Your phone checks everything itself."
---

In short:

- The release keys never touch a computer that is online.
- Each key has one job.
- Your phone checks every update on its own. A download server cannot slip it a fake or an older system.

{{< diagram "release-path" >}}

## Where the keys live

- **Made offline.** The release keys were created on a computer with no network and no wireless radios. They have never been on a networked computer.
- **Locked in a backup.** They are kept in one encrypted backup. Opening it takes a hardware security key, its PIN and a touch. The backup files on their own are useless.
- **Out only for signing.** For a signing session the keys are unlocked into memory on the offline computer. Nothing private reaches its disk unencrypted, and switching it off clears the keys.
- **No network, ever.** The signing tools refuse to start if the computer has any network connection or swap, and check again before each step that uses a key.
- **Nothing plugged in.** The files to sign come out of the computer before the keys are unlocked. The signed files go out only after the keys are wiped from memory.

## Checks before anything is signed

The offline computer does not take a build on trust.

- **Every file is pinned.** The hash of the signing input is passed on separately and compared by hand. The tools then check every file against it.
- **Only real releases.** Release signing takes only an official user build that passed all of its device checks. It refuses Android's public test keys.
- **Boxed-in build tools.** The build's own tools run in a sandbox with no network, and see only the files and keys for their step.
- **Updates are proven first.** Each incremental update is applied offline and must give exactly the same system as the full release, byte for byte, before it is signed.
- **Checked again after.** The signed results are verified once more with public keys only.

## One key per job

| Key | What it signs |
|---|---|
| Verified boot | The system images. Your phone checks them at every start. |
| Android system keys | The system and its built-in apps, one key per role. Updates are signed with the release key among them. |
| Factory | Factory images and the release record |
| App keys | App Store, Camera and Auditor, one key each |
| Catalog | The list of apps the App Store offers |
| Release list | The releases Auditor will pair a phone with |
| Source | Commits and tags in the source code. This one is used on a developer computer, not offline. |

The public halves are on [Public keys](/documentation/keys/).

## Why a server cannot fool your phone

The two download servers only hand out files. They hold no keys, so they cannot make a file your phone will accept.

{{< diagram "update-checks" >}}

- **Signed or nothing.** The list of updates a server offers is only a hint. Only a correctly signed package can start an install.
- **Pinned connections.** Downloads use TLS pinned to the two servers, and redirects are refused.
- **No going back.** The Updater only installs newer builds. At every start, verified boot also refuses a system older than the newest security patch date the phone has seen. Two releases with the same patch date count as equal there, as on Android.

What a server can still do: see who downloads what, and hold an update back for a while. It cannot change one. [What can the servers see?](/faq/#server-privacy)

## Check it yourself

- **At every start:** the yellow warning screen shows the verified boot key ID. Compare it with [Public keys](/documentation/keys/#verified-boot-key).
- **Factory images:** check their signature with `ssh-keygen`, as the [install guide](/install/cli/#verifying-the-factory-images) shows.
- **Apps:** compare `apksigner` digests with [Public keys](/documentation/keys/#apps).
- **A running phone:** pair it with Auditor. See [Attestation explained](/documentation/attestation/).
- **Source code:** check commits and tags with `git verify-commit` and `git verify-tag`, as the [build guide](/build/#verifying-the-source) shows.
