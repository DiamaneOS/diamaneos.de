---
title: "Install"
description: "Install DiamaneOS on a supported device from the command line, lock the bootloader, or return to the stock OS."
lede: "Install DiamaneOS on a supported device with fastboot, then lock the bootloader."
---

{{< page-index >}}

## Only from this project

DiamaneOS files and install guides come only from this website and the [DiamaneOS organisation](https://github.com/DiamaneOS) on GitHub. Do not use them from anywhere else.

## Before you start

- A [supported device](/devices/) whose bootloader can be unlocked.
- A computer with Linux, macOS or Windows, and a USB data cable. Connect the phone directly, not through a hub.
- Back up your data. Unlocking, installing and locking each erase the phone.
- In the stock OS, note the build number under Settings > About phone. You need it before installing.

## Enabling OEM unlocking

In the stock OS:

1. Open Settings > About phone and tap **Build number** seven times. This turns on developer options.
2. Open Settings > System > Developer options and turn on **OEM unlocking**. The phone needs an internet connection for this.

OEM unlocking allows the bootloader to be unlocked. It does not unlock it.

## Getting fastboot

Use fastboot from Google's [Android SDK Platform-Tools](https://developer.android.com/tools/releases/platform-tools). Packages from Linux distributions are often older. Unpack the download. From the directory that holds the unpacked `platform-tools`, add it to `PATH` for the current terminal.

On Linux and macOS:

```sh
export PATH="$PWD/platform-tools:$PATH"
```

On Windows, in PowerShell:

```sh
$env:Path = "$PWD\platform-tools" + [IO.Path]::PathSeparator + $env:Path
```

Use the same terminal for every step below. On Linux, fastboot may need udev rules to reach the phone without root. Debian and Ubuntu ship them in the `android-sdk-platform-tools-common` package.

### Checking fastboot

```sh
fastboot --version
```

It prints the version and where fastboot is installed. Check that this is the `platform-tools` directory you unpacked.

## Booting into the bootloader

Turn the phone off. Hold its bootloader keys, listed under [supported devices](/devices/), until the bootloader screen appears. Then connect the phone to the computer and check that fastboot sees it:

```sh
fastboot devices
```

It must list exactly one phone.

### If fastboot stops answering

The bootloader stops answering when a fastboot command is cut off while the phone replies, for example with Ctrl+C. Let every command finish. To recover, hold the power button until the phone turns off, then start it in the bootloader again.

## Unlocking the bootloader

The phone needs two unlocks. The first unlocks the bootloader. The second unlocks the critical partitions, which hold the firmware the install writes. Each one erases all data on the phone.

```sh
fastboot flashing unlock
```

The bootloader asks for confirmation on the phone's screen. Select the unlock choice with the volume buttons and confirm with the power button. The phone erases all data. If it restarts, start it in the bootloader again.

```sh
fastboot flashing unlock_critical
```

Confirm on the phone again. The phone erases all data again. Then check that both unlocks are done:

```sh
fastboot oem device-info
```

It must show `Device unlocked: true` and `Device critical unlocked: true`.

## Getting the factory images

Download the factory images for your device and their signature file, which ends in `.sig`, only from this project.

### Verifying the factory images

Check the signature before you unpack the images. First get DiamaneOS's [factory key](/documentation/keys/#factory-images):

```sh
curl --fail -O {{< site-url "keys/factory.allowed_signers" >}}
```

Then check the signature. Replace `FILE.zip` with the name of the factory images file:

```sh
ssh-keygen -Y verify -f factory.allowed_signers -I diamaneos -n "factory images" -s FILE.zip.sig < FILE.zip
```

- It must print `Good "factory images" signature for diamaneos with ED25519 key SHA256:efhtysP+8Tz5vKgjZT6MEfiK3h3bH2/cjW3w3cg6How`. Stop if it prints anything else.
- On Windows, run both commands in Command Prompt, not PowerShell.
- `ssh-keygen` is part of OpenSSH, which macOS and Windows include. On Linux it comes with the OpenSSH client package.

Then unpack the images and open a terminal in the directory that holds `flash-all.sh`. The install scripts, `flash-all.sh` and `flash-all.bat`, check every file against the `SHA256SUMS` file before they write anything.

### Checking the firmware release

The install writes the device maker's firmware of the stock release DiamaneOS is built on. Its first lines name that release:

```sh
head -n 5 flash-all.sh
```

On Windows, open `flash-all.bat` in a text editor instead. Compare the release with the build number you noted in the stock OS. If the phone runs a newer stock release, do not install.

## Installing DiamaneOS

With the phone in the bootloader, run the install script.

On Linux and macOS:

```sh
bash flash-all.sh
```

On Windows:

```sh
.\flash-all.bat
```

- It checks that the phone is the device the images are for, in the bootloader with both unlocks done.
- It erases the phone, writes the device maker's firmware and then DiamaneOS.
- For the system partitions it restarts the phone into fastbootd, then back into the bootloader. It waits for each restart on its own.
- It installs DiamaneOS's verified boot key and restarts the phone into the bootloader, ready for the lock. fastboot may warn about a partition size of 0 when it writes the key. That is normal.
- Do not touch the phone or the cable until the script ends.
- If the phone does not come back within a few minutes of a restart, hold its [bootloader keys](/devices/) until the bootloader screen appears. The script then goes on or stops with a message. Run it again only once it has stopped.

### If the install fails

- **A check failed before the first write.** Nothing on the phone changed. Fix what the message names and run the script again. A file that does not match `SHA256SUMS` is damaged or altered. Download the factory images again.
- **A write failed or the phone stopped answering.** Do not start Android. Start the phone in the bootloader with its bootloader keys and run the script again. It writes everything again from the start.
- **It fails at the same place twice.** Try another USB port or cable, without a hub.
- **Never do these to fix a failed install:** lock the bootloader, run `fastboot -w`, erase partitions or switch slots.
- If it still fails, keep the script's full output and [report the problem](/faq/#reporting-problems).

## Locking the bootloader

Locking turns on full verified boot with DiamaneOS's key. Lock right after the install, before Android first starts. It takes two locks, in the device maker's order: first the critical partitions, then the bootloader.

- **Finish every lock step before starting Android.** Do them one after another. Android's setup turns OEM unlocking off, and the bootloader can then no longer be locked safely.
- **Keep verified boot on.** Never install with options that turn it off. Locking without it is pointless.
- **Stop if something fails.** Do not repeat a lock command after an error.

First check that the bootloader can be unlocked again later:

```sh
fastboot flashing get_unlock_ability
```

It must report 1. If it reports 0, do not lock. Run `flash-all.sh` again, which ends in the bootloader, and check again.

Then lock the critical partitions:

```sh
fastboot flashing lock_critical
```

Confirm on the phone with the volume and power buttons. The phone erases all data and restarts. Hold its bootloader keys while it restarts, so it comes back to the bootloader. Android must not start between the two locks.

If Android starts, do not lock the bootloader. It stays unlocked. To lock, start the phone in the bootloader and run `flash-all.sh` again, which first asks to unlock the critical partitions. Then lock straight after.

Check that the critical partitions are locked and that unlocking is still allowed:

```sh
fastboot oem device-info
fastboot flashing get_unlock_ability
```

It must show `Device critical unlocked: false` and report 1. If not, do not lock.

Then lock the bootloader:

```sh
fastboot flashing lock
```

Confirm on the phone again. The phone erases all data and starts DiamaneOS.

- From now on, each start shows a yellow warning screen with the ID of the key the OS is signed with. This is expected: DiamaneOS boots with its own key, not the device maker's.
- Compare that ID with the [verified boot key ID](/documentation/keys/#verified-boot-key). It must match.
- An orange warning screen means the bootloader is still unlocked. Start the phone in the bootloader, install again and lock straight after.

## Disabling OEM unlocking

The last setup screen offers to turn OEM unlocking off, and that choice is selected. Keep it. With OEM unlocking off, the bootloader refuses `fastboot flashing unlock`. Turn it on again only when you want to unlock the bootloader, for example to return to the stock OS.

## Returning to the stock OS

This replaces DiamaneOS with the device maker's stock OS and erases all data. The notes for your device under [supported devices](/devices/) link the device maker's factory images and install guide.

### Getting the stock factory image

Download the device maker's factory image for your phone, as its install guide describes. Check its SHA-256 against the checksum the device maker publishes:

```sh
sha256sum FILE.zip
```

On macOS, use `shasum -a 256 FILE.zip`. Stop if the checksum differs.

Use the stock release whose firmware the DiamaneOS install wrote, or a newer one. Firmware older than the phone runs can leave it unable to start.

### Unlocking

If the bootloader is locked:

1. In DiamaneOS, turn on developer options under Settings > About phone by tapping **Build number** seven times.
2. Turn on **OEM unlocking** under Settings > System > Developer options.
3. Turn the phone off and start it in the bootloader. Run `fastboot flashing unlock` and confirm on the phone. This erases all data.
4. Hold the bootloader keys while the phone restarts, so it comes back to the bootloader. If Android starts, turn the phone off and start it in the bootloader.

A locked DiamaneOS has its critical partitions locked too, and the stock install writes firmware on them. If `fastboot oem device-info` shows `Device critical unlocked: false`, run `fastboot flashing unlock_critical`. Confirm on the phone and come back to the bootloader the same way.

`fastboot oem device-info` must then show `Device unlocked: true` and `Device critical unlocked: true`.

### Installing the stock OS

In the bootloader, with the bootloader unlocked:

```sh
fastboot oem reset-rollback
```

It clears the stored rollback indexes, so an older stock release can boot locked. The bootloader refuses it while locked.

Then install the stock OS with the device maker's own script from the factory image, as its guide describes. If you want to lock the bootloader on the stock OS, the phone must stay in the bootloader after the install. The [notes for your device](/devices/) say how, and what to do if the install stops.

### Locking on the stock OS

Lock only with the stock OS installed, and before Android starts.

1. Remove DiamaneOS's key, so the phone no longer trusts it:

   ```sh
   fastboot erase avb_custom_key
   ```

2. Check that `fastboot getvar current-slot` reports the slot that the device maker's script activated. The script names it in its output. `fastboot oem device-info` must show both unlocks and `Verity mode: true`.
3. Check that `fastboot flashing get_unlock_ability` reports 1. If it reports 0, do not lock.
4. Lock the critical partitions and confirm on the phone. Hold the bootloader keys while it restarts, so it comes back to the bootloader without starting Android:

   ```sh
   fastboot flashing lock_critical
   ```

5. Check again that `fastboot flashing get_unlock_ability` reports 1 and that `fastboot oem device-info` shows `Device critical unlocked: false`. If not, do not lock.
6. Lock the bootloader and confirm on the phone. This erases all data:

   ```sh
   fastboot flashing lock
   ```

7. Start the stock OS. It starts without a warning screen. Then turn off **OEM unlocking** under Settings > System > Developer options.

This is the device maker's order: the critical partitions first, then the bootloader.
