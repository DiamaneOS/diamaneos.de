---
title: "Build DiamaneOS"
description: "Build DiamaneOS from source: host, dependencies, source and its signatures, vendor files, user and development builds, checks, installation and signing with your own keys."
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
  lib32gcc-s1 hostname ca-certificates util-linux kmod binutils openssl make perl curl
```

This is the only step that needs `sudo`. Everything else runs as your own user. The build environment file for each device in the tools' [config](https://github.com/DiamaneOS/diamaneos-tools/tree/main/config) records the tested package versions.

## Getting the source

Make a directory for the source, then initialise it from the [manifest repository](https://github.com/DiamaneOS/platform_manifest.git) and sync it:

```sh
mkdir -p ~/diamaneos
cd ~/diamaneos
repo init -u https://github.com/DiamaneOS/platform_manifest.git -b android17
repo sync -j8
```

- The [DiamaneOS manifest](https://github.com/DiamaneOS/platform_manifest/tree/android17) takes GrapheneOS and AOSP projects at the exact commits of the GrapheneOS release it is based on. It adds the device projects and the DiamaneOS forks.
- The build tools come with the source at `tools/diamaneos`. Run them from there, so the tools match the source.
- Any directory works. Images, logs and build state go next to it, to `~/diamaneos-build` here. `--workspace DIR` puts them somewhere else.
- Run the commands below from the source directory.

### Smaller download

Add `--depth=1` to `repo init` and sync with `repo sync -c --no-tags -j8`. With `build all`, pass `--shallow` the first time. The checkout then has no history. This saves roughly half of the download and disk space. Moving to a newer release later downloads more.

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
- Run them in a DiamaneOS project of the checkout, such as `tools/diamaneos`. For the manifest, run them in `.repo/manifests`.
- The smaller download fetches no tags. Fetch the tag first with `git fetch --depth=1 diamaneos tag TAG`, or with `origin` instead of `diamaneos` in `.repo/manifests`.
- Commits taken from GrapheneOS and AOSP keep their own signatures or have none.

## Vendor files

Replace `<codename>` with your device's codename:

{{< codenames >}}

```sh
tools/diamaneos/bin/diamaneos build vendor <codename>
```

- It downloads the device maker's factory package from its official host and checks its size and SHA-256.
- It takes the vendor files the source selects out of that package and checks each one against its recipe.
- `--factory-zip FILE` uses a copy you already have. The copy must have the same size and SHA-256.
- It installs them in the source and prints the commands to run next.
- Run again, it makes the vendor files only when their recipe changed.
- GrapheneOS's vendor extraction for Pixel phones does not apply.

## Building a user build

After the vendor files:

```sh
source build/envsetup.sh
lunch <codename>-cur-user
m droid target-files-package otatools-package
tools/diamaneos/bin/diamaneos build package
```

- `m droid target-files-package otatools-package` builds the images, the target-files archive and the host tools. A plain `m` builds the images only.
- Keep `droid`. Without it the target-files archive lacks the vendor SELinux policy, and the checks of `build package` fail.
- `build package` refuses a target-files archive that lacks files `m` installed after it, or holds other bytes for them. Remove the directory it names and run `m droid target-files-package otatools-package` again.
- For a build you keep, remove what earlier builds left first, as GrapheneOS's build guide says: `rm -r out` before `m`.
- `build package` checks that `out/` holds a build of this source with these vendor files, writes the image set and checks it.
- It runs its tools from the build's own `otatools.zip`.
- `build.json` marks the set as built by hand.

### Or all steps in one command

Instead of the vendor files and the build by hand, one command can do everything. It replaces those steps and does not follow them.

```sh
tools/diamaneos/bin/diamaneos build all
```

- It runs the source sync, the vendor files, the Android build and the packaging, then checks the images. `user` is the default variant.
- Compilation runs without network access. If the host cannot do that, the build stops. `--allow-network` builds anyway and records it in `build.json`.
- After a stop, run the same command again. Finished steps are skipped. `--dry-run` shows what is left.
- At the end it prints the image directory, such as `~/diamaneos-build/images/20261003-user-3f9a1c2b7d`.
- Leave out `--official`. It adds the Updater with DiamaneOS's update server, for the project's own builds.

## Development builds

Run `lunch <codename>-cur-userdebug` instead, or `build all --variant userdebug`.

- `userdebug` adds root debugging over adb. Use it for development only.
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
- A failed check stops the command, and the image set moves aside to `<build>.failed`. The report names each failed check and why it exists.
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

These commands sign every build with Android's public test keys. Anyone can sign images with them. Keep the bootloader unlocked while such a build is installed, and never lock it. To lock the phone, [sign the build with your own keys](#signing-with-your-own-keys) first.

### First install

Follow the [command-line install guide](/install/cli/) up to [unlocking the bootloader](/install/cli/#unlocking-the-bootloader). Then, with the phone in the bootloader:

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

## Signing with your own keys

Sign a build with keys of your own to lock the phone with them. The steps follow [GrapheneOS's build guide](https://grapheneos.org/build). Run them from the source directory, after `build all` or `build package`.

### Generating keys

Generate the keys once and keep them. Another key set needs a new install, which erases the phone. Replace `<codename>` with your device's codename and `YourName` with a name for the certificates:

```sh
DEVICE=<codename>
CN=YourName
mkdir -p keys/$DEVICE && cd keys/$DEVICE
for role in releasekey platform shared media networkstack bluetooth sdk_sandbox gmscompat_lib nfc; do
  ../../development/tools/make_key "$role" "/CN=$CN/"
done
openssl genrsa 4096 | openssl pkcs8 -topk8 -scrypt -out avb.pem
../../external/avb/avbtool.py extract_public_key --key avb.pem --output avb_pkmd.bin
ssh-keygen -t ed25519 -f id_ed25519
cd ../..
```

- Give every key the same passphrase. `script/decrypt-keys` expects that.
- `avb_pkmd.bin` is your verified boot key. Its ID is its SHA-256, from `sha256sum keys/$DEVICE/avb_pkmd.bin`.
- `id_ed25519` signs the build's check report and the factory images.

### Signing a build

Name the build and a directory for the signed files:

```sh
IMAGES=$(readlink -f ~/diamaneos-build/images/latest)
REPORT=$IMAGES.verify.json
SIGN=~/diamaneos-signing/$(basename "$IMAGES")
mkdir -p "$SIGN"
```

Write the inventory of your public keys and sign the check report:

```sh
tools/diamaneos/bin/diamaneos signing inventory --key-dir keys/$DEVICE --identity "$CN" \
  --target-files "$IMAGES/target-files.zip" --output "$SIGN/trust"
ssh-keygen -Y sign -n diamaneos-build-verification -f keys/$DEVICE/id_ed25519 "$REPORT"
```

Prepare the signing plan:

```sh
tools/diamaneos/bin/diamaneos signing prepare \
  --build-record "$IMAGES/build.json" --verification-report "$REPORT" \
  --verification-signature "$REPORT.sig" --target-files "$IMAGES/target-files.zip" \
  --resolved-manifest "$IMAGES/resolved-manifest.xml" --otatools "$IMAGES/otatools.zip" \
  --source-root "$PWD" --keys "$SIGN/trust/inventory.json" \
  --scratch "$SIGN/scratch" --output "$SIGN/plan.json"
```

Sign the build and make its full update package, with the keys decrypted in memory:

```sh
unzip -q "$IMAGES/otatools.zip" -d "$SIGN/otatools"
KEY_DIR=$(mktemp -d /dev/shm/keys.XXXXXXXXXX)
cp keys/$DEVICE/* "$KEY_DIR" && script/decrypt-keys "$KEY_DIR"
tools/diamaneos/bin/diamaneos signing command --plan "$SIGN/plan.json" \
  --target-files "$IMAGES/target-files.zip" --signed-target-files "$SIGN/target-files.zip" \
  --signer "$SIGN/otatools/bin/sign_target_files_apks" --key-dir "$KEY_DIR" \
  --source-root "$PWD" --ota "$SIGN/$DEVICE-ota_update.zip" > "$SIGN/sign.sh"
PATH="$SIGN/otatools/bin:$PWD/prebuilts/build-tools/linux-x86/bin:$PWD/prebuilts/build-tools/path/linux-x86:$PWD/prebuilts/jdk/jdk21/linux-x86/bin:$PATH" \
  sh -e "$SIGN/sign.sh"
rm -rf "$KEY_DIR"
```

- `signing command` only prints the signing commands. Read `sign.sh` before you run it.
- It refuses a plan, source or target files that changed since `signing prepare`.

Make the factory images and sign them:

```sh
tools/diamaneos/bin/diamaneos signing factory --plan "$SIGN/plan.json" \
  --build-record "$IMAGES/build.json" --verification-report "$REPORT" \
  --verification-signature "$REPORT.sig" --target-files "$IMAGES/target-files.zip" \
  --resolved-manifest "$IMAGES/resolved-manifest.xml" --signed-target-files "$SIGN/target-files.zip" \
  --otatools "$IMAGES/otatools.zip" --source-root "$PWD" --keys "$SIGN/trust/inventory.json" \
  --scratch "$SIGN/scratch" --images-archive "$SIGN/images.zip" --output "$SIGN/$DEVICE-factory.zip"
ssh-keygen -Y sign -n "factory images" -f keys/$DEVICE/id_ed25519 "$SIGN/$DEVICE-factory.zip"
```

- The `build.json` of the factory images records the signing as `own-keys`.
- A build of changed source lists its changes there too.

### Installing and locking

Start with the bootloader unlocked, as for the [first install](#first-install). Then unpack the factory images and run their install script:

```sh
unzip -q "$SIGN/$DEVICE-factory.zip" -d "$SIGN/factory"
cd "$SIGN"/factory/*/
bash flash-all.sh
```

- It installs the images and your verified boot key, then stops in the bootloader.
- Lock straight away, as the install guide's [locking steps](/install/cli/#locking-the-bootloader) describe.
- From then on the warning screen at each start shows the ID of your key. It must match the SHA-256 of your `avb_pkmd.bin`.

### Updating a build of your own

Builds of your own have no Updater. It comes only with DiamaneOS's official builds. To update, build the newer source and sign it with the same keys. Then install its full update package from recovery, as on GrapheneOS:

1. Start the phone in recovery from the bootloader menu and choose "Apply update from ADB".
2. Send the update package:

   ```sh
   adb sideload "$SIGN/$DEVICE-ota_update.zip"
   ```

- Recovery installs only update packages signed with your `releasekey`.
- The phone keeps its data.

An update server of your own is a source change, as on GrapheneOS:

- `vendor/diamaneos/download-policy/client/de/diamaneos/downloads/DownloadPolicy.java` builds the update addresses in `url()`.
- `vendor/diamaneos/overlay/DiamaneOSUpdaterOverlay/res/xml/network_security_config.xml` names the server domains and their TLS pins.
- `vendor/diamaneos/product.mk` adds the Updater only when `DIAMANEOS_OFFICIAL_BUILD` is `true`.

## Troubleshooting

- A failed step names its log in `~/diamaneos-build/logs/`. Fix the cause and run the same command again.
- If a signature or hash does not match, do not work around it. Check your network, then report it.
- The [build reference](https://github.com/DiamaneOS/diamaneos-tools/blob/main/docs/BUILD.md#troubleshooting) lists common errors and what to do.

## More detail

- The [build quickstart](https://github.com/DiamaneOS/diamaneos-tools/blob/main/docs/BUILDING.md) has the same steps in short.
- The [build reference](https://github.com/DiamaneOS/diamaneos-tools/blob/main/docs/BUILD.md) describes each step, its checks and its records.
- The [signing reference](https://github.com/DiamaneOS/diamaneos-tools/blob/main/docs/SIGNING.md) describes each signing command and its checks.
