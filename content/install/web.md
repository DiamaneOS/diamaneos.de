---
title: "Web installation"
description: "Install DiamaneOS on a supported device with the web installer, lock the bootloader, and what to do when a step fails."
lede: "Install DiamaneOS on a supported device from a browser, then lock the bootloader."
---

The [web installer](https://install.diamaneos.de) installs DiamaneOS over USB from a browser. It runs the same steps as the install script of the factory images and checks every file before it writes anything.

Keep this guide open in another tab or on another device. While a phone is connected, the installer asks before its page is left.

{{< page-index >}}

## Before you start

- A [supported device](/devices/) whose bootloader can be unlocked.
- A computer with a Chromium-based browser, such as Chrome, Chromium or Edge. Other browsers have no WebUSB, which the installer needs.
- At least 2 GB of free memory, and free disk space for the download and its unpacked files.
- A USB data cable. Connect the phone directly, not through a hub, and connect no other phone.
- Back up your data. Unlocking, installing and locking each erase the phone.
- In the stock OS, note the build number under Settings > About phone. You need it before installing.

### On Linux

- The browser needs the udev rules for Android devices to reach the phone. Debian and Ubuntu ship them in the `android-sdk-platform-tools-common` package, Arch Linux in `android-udev`.
- fwupd can take over the phone's USB connection. Stop it before you start:

  ```sh
  sudo systemctl stop fwupd.service
  ```

## Enabling OEM unlocking

In the stock OS:

1. Open Settings > About phone and tap **Build number** seven times. This turns on developer options.
2. Open Settings > System > Developer options and turn on **OEM unlocking**. The phone needs an internet connection for this.

OEM unlocking allows the bootloader to be unlocked. It does not unlock it.

## Booting into the bootloader

Turn the phone off. Hold its bootloader keys, listed under [supported devices](/devices/), until the bootloader screen appears. The installer calls this screen Fastboot Mode.

## Connecting the phone

1. Open the [web installer](https://install.diamaneos.de) and connect the phone to the computer.
2. Press **Connect** and choose the phone in the browser's dialog.
3. The installer shows the phone's state: whether the bootloader and the critical partitions are unlocked, and whether unlocking is allowed.

The phone restarts several times during the install. The installer reconnects on its own. If it asks, press **Connect again** and choose the phone. Steps the phone reports as done are greyed out.

## Unlocking the bootloader

The phone needs two unlocks. The first unlocks the bootloader. The second unlocks the critical partitions, which hold the firmware the install writes. Each one erases all data on the phone.

1. Press **Unlock bootloader**. On the phone, select the unlock choice with the volume buttons and confirm with the power button.
2. The phone erases all data and restarts. Hold its bootloader keys while it restarts, so it comes back to the bootloader before Android starts.
3. Once the installer shows the phone in the bootloader again, press **Unlock critical partitions**. Confirm on the phone the same way. The phone erases all data again and restarts. Bring it back to the bootloader as before.

Android must not start between the two unlocks. Its first start turns OEM unlocking off, and the critical partitions can then not be unlocked. If Android starts, turn the phone off, start it in the bootloader and press **Connect**.

## Getting the image set

The installer needs the image set: the factory images for the phone. Get it in one of two ways.

- **Download release** gets the current stable release for the connected phone from this project. The installer checks its signature with DiamaneOS's factory key before it reads it.
- **Choose folder** or **Choose files** reads factory images you downloaded from this project and unpacked. The browser asks whether to upload them, but nothing leaves the computer.

Either way, the installer checks every file it writes against the image set's `SHA256SUMS`. It then names the release and the device maker's firmware release it writes.

## Installing DiamaneOS

The install writes the device maker's firmware of the stock release DiamaneOS is built on, and the installer names that release. Compare it with the build number you noted. If the phone runs a newer stock release, do not install. Otherwise tick the box that confirms this.

Press **Install**. It erases the phone. Do not touch the phone or the cable, and keep the installer page open, until the installer reports the end.

- In the bootloader it writes the device maker's firmware and DiamaneOS's boot images.
- The phone then restarts into fastbootd, which writes the system partitions. fastbootd is a new USB device to the browser. If the installer shows **Connect again**, wait until the phone shows fastbootd, press it and choose the phone.
- The phone returns to the bootloader for the remaining partitions. If it is back and the installer does not go on, press **Connect again**.
- It installs DiamaneOS's verified boot key and restarts the phone into the bootloader, ready for the lock.

At the end the installer reports that the phone waits in Fastboot Mode. Do not start Android. Lock it straight away.

## Locking the bootloader

Locking turns on full verified boot with DiamaneOS's key. It takes two steps, in the device maker's order: first the critical partitions, then the bootloader.

- **Finish both steps before starting Android.** Android's setup turns OEM unlocking off, and the bootloader can then no longer be locked safely.
- **Stop if something fails.** Do not repeat a lock after an error.
- The installer offers the lock only straight after its install, while the phone stays connected. If the phone restarts or is unplugged in between, install again and lock straight after.
- Before each step the installer checks that the phone still allows unlocking. It never locks a phone that could not be unlocked again.

1. Press **Lock critical partitions**. Confirm on the phone with the volume and power buttons. The phone erases all data and restarts.
2. Hold the bootloader keys while it restarts, so it comes back to the bootloader before Android starts. If it does not come back in time, the installer stops and leaves the bootloader unlocked.
3. The installer checks that the critical partitions are locked. Then press **Lock bootloader** and confirm on the phone again. The phone erases all data and starts DiamaneOS.

From now on, each start shows a yellow warning screen with the ID of the key the OS is signed with.

- This is expected: DiamaneOS boots with its own key, not the device maker's.
- An orange warning screen means the bootloader is still unlocked. Start the phone in the bootloader, install again and lock straight after.

## Disabling OEM unlocking

The last setup screen offers to turn OEM unlocking off, and that choice is selected. Keep it. With OEM unlocking off, the bootloader refuses to unlock. Turn it on again only when you want to unlock the bootloader, for example to return to the stock OS.

## If a step fails

When the install or a lock fails, the installer shows the error and a **What to do now** link. It leads to the installer's [recovery page](https://install.diamaneos.de/recovery.html), which covers each case.

- **A check failed before the first write.** Nothing on the phone changed. Fix what the message names and try again.
- **A write failed or the phone stopped answering.** Do not start Android. Start the phone in the bootloader with its bootloader keys, connect it and press **Install** again. The install writes everything again from the start.
- **It fails at the same place twice.** Try another USB port or cable, without a hub.
- **Never lock the bootloader to fix a failed install.** A locked phone that does not start may not be recoverable.

The **Log** at the end of the installer page records each step. It holds no serial numbers. Press **Copy** or **Save** and add it when you [get help](/install/#getting-help).

## Returning to the stock OS

Returning to the stock OS uses fastboot from the command line. Follow [returning to the stock OS](/install/cli/#returning-to-the-stock-os) in the command-line guide. It replaces DiamaneOS with the device maker's stock OS and erases all data.
