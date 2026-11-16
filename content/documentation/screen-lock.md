---
title: "Screen lock explained"
description: "Why the lock matters so much on the Fairphone 6, how the generated passphrase works and how long guessing would take."
lede: "On this phone, your lock is what keeps your data safe."
---

In short:

- The FP6 has no separate security chip.
- If its secure area were ever broken, only your lock would stand between someone and your data.
- A generated passphrase holds even then. A PIN does not.

{{< diagram "lock-path" >}}

## How long guessing would take

The setup screens assume an attacker who tries a million guesses a second. Today that takes more than 10,000 top graphics cards. The times are averages.

| Lock | Time to guess |
|---|---|
| 6-digit PIN | seconds |
| 12-digit random PIN | about 5.7 days |
| Short passphrase: 6 words, 3 letters each | about 63,000 years |
| Passphrase of 5 words | about 440,000 years |
| Generated 20-digit PIN | about 1.5 million years |
| Passphrase of 6 words (the default) | about 3.4 billion years |

These times only hold for a lock the phone generated. One you make up is much easier to guess. Machines built for the job, which only a government could pay for, might be a thousand times faster.

## Why each guess is so slow

Android turns your lock into a key with a deliberately slow step. On stock Android that step uses about half a megabyte of memory and stays under 50 milliseconds. DiamaneOS makes it use 256 MiB and about a second.

Typing your lock takes about a second longer. Fingerprint unlocks skip this step. An attacker pays it on every single guess, on any computer. A lock gets this protection when you set or change it.

## The generated passphrase

- **Made for you.** Setup offers a passphrase of random words, drawn by the phone. The default is 6 words from a list of 7,772. You can pick 5 to 8.
- **The short version.** 6 words from a list where no two words start with the same 3 letters. You type only those first 3 letters of each word: 18 letters, no spaces. Nothing is lost, because 3 letters always name exactly one word.
- **A PIN is still possible.** Setup first shows a screen that explains the risk. A 20-digit PIN the phone generates counts as strong too.
- **What counts as strong.** A generated passphrase or PIN, or a password of 20 or more characters. A pattern or a PIN you choose always counts as weaker.

## Learning it

For the first 14 days the phone asks for your new lock about once a day: fingerprint stops working 24 hours after you last typed it. Only time with the phone switched on counts. After that, fingerprint works as usual.

## Day to day

- **After every restart** you need the full lock. Fingerprint only works after that first unlock.
- **Fingerprint with a second factor.** You can require a separate PIN on top of your fingerprint.
- **Auto reboot.** After 12 hours without an unlock, the phone restarts and your data is locked away again. Change it under Settings > Security & privacy > Exploit protection > Auto reboot.
- **Nothing left on unencrypted storage.** Android keeps a copy of the lock's check data on an unencrypted partition, for factory reset protection. DiamaneOS does not use that protection and does not write the copy.

See also the [known limitations](/limitations/) of the secure area.
