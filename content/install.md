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

Download the factory images for your device only from this project. Unpack them and open a terminal in the directory that holds `flash-all.sh`.

On Linux and macOS, `flash-all.sh` checks every image against the `SHA256SUMS` file before it writes anything.

The install writes the device maker's firmware of the stock release DiamaneOS is built on. Its first lines name that release:

```sh
head -n 5 flash-all.sh
```

Compare it with the build number you noted in the stock OS. If the phone runs a newer stock release, do not install.

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
- If the script stops with an error, do not start Android. Keep its full output and [report the problem](/faq/#reporting-problems).

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

Confirm on the phone with the volume and power buttons. The phone erases all data and restarts. Hold its bootloader keys while it restarts, so it comes back to the bootloader. If Android starts, start the phone in the bootloader again before going on.

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

### Unlocking

If the bootloader is locked:

1. In DiamaneOS, turn on developer options under Settings > About phone by tapping **Build number** seven times.
2. Turn on **OEM unlocking** under Settings > System > Developer options.
3. Start the phone in the bootloader and run `fastboot flashing unlock`. Confirm on the phone. This erases all data.
4. Run `fastboot flashing unlock_critical` and confirm on the phone again. The stock install writes the firmware on the critical partitions.

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

2. Check that `fastboot flashing get_unlock_ability` reports 1. If it reports 0, do not lock.
3. Lock the critical partitions, then the bootloader, as the device maker's guide does. Confirm each on the phone:

   ```sh
   fastboot flashing lock_critical
   fastboot flashing lock
   ```
4. Start the stock OS and turn off **OEM unlocking** under Settings > System > Developer options.
