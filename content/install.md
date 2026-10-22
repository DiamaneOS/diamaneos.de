---
title: "Install"
description: "Choose how to install DiamaneOS on a supported device: the web installer or the command line."
lede: "Install DiamaneOS on a supported device from a browser or from the command line."
---

There are two ways to install DiamaneOS. Both write the same factory images in the same steps and end with a locked bootloader.

- **[Web installation](/install/web/)** is recommended for most people. It needs a Chromium-based browser and a USB cable.
- **[Command-line installation](/install/cli/)** uses fastboot and the install script of the factory images. It suits people who are at ease in a terminal and want to run each step themselves.

## Checking the key after the install

Each start of a locked phone shows a yellow warning screen with the ID of the key the OS is signed with. For DiamaneOS it is the [verified boot key ID](/documentation/keys/#verified-boot-key):

```text
5c4c94ba54e9f4fe81dcfd77e9b919204f0a493593a2677b50498cbcb6cd8f8d
```

Another ID means the phone runs an OS signed with another key.

## Only from this project

DiamaneOS files, the web installer and the install guides come only from diamaneos.de and its subdomains, and from the [DiamaneOS organisation](https://github.com/DiamaneOS) on GitHub. Do not use them from anywhere else.

## Getting help

If a step fails, follow your guide's section on failed installs first. If that does not help, report the problem on the [issue tracker](https://github.com/DiamaneOS/issue-tracker/issues). Name the step that failed and add the web installer's log or the install script's full output. The [FAQ](/faq/#reporting-problems) says where other reports go.
