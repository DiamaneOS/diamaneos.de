---
title: "Build DiamaneOS"
description: "Build DiamaneOS from source: host, dependencies, source and its signatures, vendor files, user and development builds, checks and installation."
lede: "Build DiamaneOS from source, check the result and install it."
---

{{< page-index >}}

## Host requirements

- Linux on x86-64. Debian 13 is tested.
- 16 CPU cores or more. 8 cores work, slowly.
- 64 GB of memory. 32 GB is the minimum.
- About 500 GB free on an SSD, with a case-sensitive filesystem such as ext4, xfs or btrfs.
- A fast connection. The first sync downloads 100 to 150 GB.
- Unprivileged user namespaces and util-linux 2.38 or newer. Compilation runs inside one, without network access. Debian allows them by default. Some systems restrict them, such as Ubuntu 24.04 through AppArmor. The build then stops and says why.

The build checks the host before each step, including the free disk space the step needs.

## Dependencies

`repo` is in Debian's `contrib` section. Add `contrib` to the `Components:` line in `/etc/apt/sources.list.d/debian.sources`. Then install the packages:

```sh
sudo apt update
sudo apt install git git-lfs repo python3 python3-jsonschema gnupg openssh-client \
  rsync zip unzip diffutils fontconfig fonts-dejavu-core gperf libc6-dev-i386 \
  lib32gcc-s1 hostname ca-certificates util-linux kmod binutils openssl make perl
```

This is the only step that needs `sudo`. Everything else runs as your own user. The build environment file for each device in the tools' [config](https://github.com/DiamaneOS/diamaneos-tools/tree/main/config) records the tested package versions.

## Getting the source

Make a directory for the source, then initialise it from the [manifest repository](https://github.com/DiamaneOS/platform_manifest.git) and sync it:

```sh
mkdir -p ~/diamaneos-build/src
cd ~/diamaneos-build/src
repo init -u https://github.com/DiamaneOS/platform_manifest.git -b android17
repo sync -j8
```

- The [DiamaneOS manifest](https://github.com/DiamaneOS/platform_manifest/tree/android17) takes GrapheneOS and AOSP projects at the exact commits of the GrapheneOS release it is based on. It adds the device projects and the DiamaneOS forks.
- The build tools come with the source at `tools/diamaneos`. Run them from there, so the tools match the source.
- The tools use the directory above the checkout as their workspace. Images, logs and build state go to `~/diamaneos-build`.
- Run the commands below from the `src` directory.

### Smaller download

Add `--depth=1` to `repo init`, sync with `repo sync -c --no-tags -j8` and pass `--shallow` to the first `build all`. The checkout then has no history. This saves roughly half of the download and disk space. Moving to a newer release later downloads more.

### Updating the source

`build all` syncs the source itself each time. For a build by hand, sync with:

```sh
repo sync --force-sync -j8
```

`--force-sync` lets `repo` replace a project that now comes from another repository at the same path. DiamaneOS rebases its branches onto new GrapheneOS releases. Rebase your own commits onto the new branch tips.

## Verifying the source

DiamaneOS's own commits and its release tags are signed with an SSH key. Its fingerprint is `SHA256:OHUN0l/oDXtrLvDWWH/76gM5yjl7JqCx6KdgO7zB62Y`. The key is registered on GitHub, which marks these commits Verified.

Get the [allowed signers file](/allowed_signers.txt) and look at it:

```sh
curl --fail --create-dirs -o ~/.ssh/diamaneos_allowed_signers {{< site-url "allowed_signers.txt" >}}
cat ~/.ssh/diamaneos_allowed_signers
```

It must hold exactly this line:

```text
abhinav.jhanwar@proton.me ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIIdAD9ESFMA9yAMy7AUMwe++dHPND/7l8TMCdS4ZWTQG
```

Then check a commit or a release tag in a DiamaneOS repository. Replace `TAG` with the tag's name:

```sh
git -c gpg.ssh.allowedSignersFile=~/.ssh/diamaneos_allowed_signers verify-commit HEAD
git -c gpg.ssh.allowedSignersFile=~/.ssh/diamaneos_allowed_signers verify-tag TAG
```

- A good signature prints `Good "git" signature for abhinav.jhanwar@proton.me` with the fingerprint above, and the command exits with 0.
- "No principal matched" or any other error means the check failed, even after a line that starts with "Good".
- To check the manifest of a `repo` checkout, run the commands in `.repo/manifests`.
- Commits taken from GrapheneOS and AOSP keep their own signatures or have none.

## Vendor files

```sh
tools/diamaneos/bin/diamaneos build vendor
```

- It downloads the device maker's factory package from its official host and checks its size and SHA-256.
- It takes the vendor files the source selects out of that package and checks each one against its recipe.
- `--factory-zip FILE` uses a copy you already have. The copy must have the same size and SHA-256.
- Run again, it makes the vendor files only when their recipe changed.
- GrapheneOS's vendor extraction for Pixel phones does not apply.

`build all` runs this step itself.

## Building a user build

### In one command

```sh
tools/diamaneos/bin/diamaneos build all
```

- It syncs the source, makes the vendor files, compiles, packages the images and checks them. `user` is the default variant.
- Only the source sync and the factory package download use the network. Compilation runs without network access.
- If the host cannot compile without network access, the build stops. `--allow-network` builds anyway and records that in `build.json`.
- Each long command prints a log file to follow with `tail -f`.
- After a stop, run the same command again. Finished steps are skipped.
- `--dry-run` shows what is left and changes nothing. `--from vendor` builds again without syncing.
- At the end it prints the image directory, such as `~/diamaneos-build/images/20261003-user-3f9a1c2b7d`. `~/diamaneos-build/images/latest` points to the newest one.
- Leave out `--official`. It adds the Updater with DiamaneOS's update server, for the project's own builds.

### By hand

The plain Android build works too. Replace `<codename>` with your device's codename:

{{< codenames >}}

```sh
tools/diamaneos/bin/diamaneos build vendor
source build/envsetup.sh
lunch <codename>-cur-user
m target-files-package otatools-package
tools/diamaneos/bin/diamaneos build package
```

- `build package` checks that `out/` holds a build of this source with these vendor files. It then writes the image set and checks it.
- `build.json` marks such a set as built by hand and not reproducible.
- A plain `m` builds the images only. `build package` also needs the target-files and otatools packages.

## Development builds

```sh
tools/diamaneos/bin/diamaneos build all --variant userdebug
```

- `userdebug` adds root debugging over adb. Use it for development only.
- Give `build all` the same `--variant` each time. Another variant builds Android again.
- By hand, run `lunch <codename>-cur-userdebug` instead.
- The variant changes debugging, not signing. Neither variant is a signed release.

## Checking a build

Each image directory holds the images and the record of what they were made from:

- `build.json`: the manifest commit, the kernel prebuilts commit, the vendor inputs, the tools commit and more.
- `resolved-manifest.xml`: the exact commit of every project.
- `SHA256SUMS`: the hash of every file.

`build all` ends by checking the image set. To check it again:

```sh
tools/diamaneos/bin/diamaneos build verify
```

- It checks the hashes, the verified boot chain, the kernel and its arguments, the vendor files, the firmware and the device rules.
- It writes its report, `<build>.verify.json`, next to the image directory.
- For a build that is not official, failed checks do not stop the command. Read the report. It names each failed check and why it exists.
- Do not edit recorded hashes, remove checks or mix files from different builds to make a check pass.

### Reproducing a build

```sh
tools/diamaneos/bin/diamaneos build all --variant user \
  --resolved-manifest DIR/resolved-manifest.xml --build-json DIR/build.json
```

- `DIR` is the image directory of the build to reproduce. Give its variant.
- The sync checks out the recorded manifest commit and every project at the commit the resolved manifest names. It then checks that the source matches the record.
- Later `build all` runs keep that source. `build sync` moves back to the head of the branch.
- The same inputs are meant to give identical partitions on any host. No command here compares two hosts' builds, so matching records and passing checks do not prove a bit-for-bit match.

## Installing your build

These commands sign every build with Android's public test keys. Anyone can sign images with them. Keep the bootloader unlocked while such a build is installed, and never lock it.

### First install

Follow the [install guide](/install/) up to [unlocking the bootloader](/install/#unlocking-the-bootloader). Then, with the phone in the bootloader:

```sh
cd ~/diamaneos-build/images/latest
bash flash-all.sh
```

- To install from another computer, copy the whole image directory there. On Windows, run `flash-all.bat`.
- `flash-all.sh` checks the phone and every image first. It then erases the phone, installs the image set and starts DiamaneOS.
- For the system partitions it restarts the phone into fastbootd, then back into the bootloader. It waits for each restart on its own.
- It writes the device maker's firmware of the release the vendor files come from. Do not run it on a phone that already runs a newer stock release.
- Skip the locking steps of the install guide.
- Never run `fastboot -w` or `fastboot erase`. The script flashes empty images instead.

### Updates that keep data

```sh
tools/diamaneos/bin/diamaneos flash-steps --since ~/diamaneos-build/images/PREVIOUS
```

- `PREVIOUS` is the image directory of the build on the phone.
- It prints the fastboot commands for the images that changed. It runs no fastboot command itself.
- It adds firmware steps only when the new set carries newer firmware. It then needs the phone's bootloader state:

```sh
fastboot getvar all > phone.txt 2>&1
fastboot oem device-info >> phone.txt 2>&1
tools/diamaneos/bin/diamaneos flash-steps --since ~/diamaneos-build/images/PREVIOUS --phone phone.txt
```

## Troubleshooting

- A failed step names its log in `~/diamaneos-build/logs/`. Fix the cause and run the same command again.
- If a signature or hash does not match, do not work around it. Check your network, then report it.
- The [build reference](https://github.com/DiamaneOS/diamaneos-tools/blob/main/docs/BUILD.md#troubleshooting) lists common errors and what to do.

## More detail

- The [build quickstart](https://github.com/DiamaneOS/diamaneos-tools/blob/main/docs/BUILDING.md) has the same steps in short.
- The [build reference](https://github.com/DiamaneOS/diamaneos-tools/blob/main/docs/BUILD.md) describes each step, its checks and its records.
