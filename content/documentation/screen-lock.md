---
title: "Screen lock explained"
description: "Why the lock matters so much on the Fairphone 6, how the generated passphrase works, and the numbers behind it."
lede: "On this phone, your lock is what keeps your data safe."
---

In short:

- The FP6 has no separate security chip.
- If its secure area were ever broken, only your lock would stand between someone and your data.
- A generated passphrase holds even then. A PIN does not.

{{< diagram "lock-path" >}}

## How long guessing would take

The setup screens assume an attacker who tries a million guesses a second. The times are averages. Strength is the number of possible locks, as a power of two.

| Lock | Strength | Time to guess |
|---|---|---|
| 6-digit PIN | 20 bits | seconds |
| 12-digit random PIN | 40 bits | about 5.7 days |
| Short passphrase: 6 words, 3 letters each | 62 bits | about 63,000 years |
| Passphrase of 5 words | 64.6 bits | about 440,000 years |
| Generated 20-digit PIN | 66.4 bits | about 1.5 million years |
| Passphrase of 6 words (the default) | 77.5 bits | about 3.4 billion years |

These numbers only hold for a lock the phone generated. One you make up is much easier to guess. Machines built for the job, which only a government could pay for, might be a thousand times faster.

## Why each guess is so slow

Android turns your lock into the key for your data in three steps:

1. **Stretching.** Your lock goes through scrypt, a function built to be slow and to need a lot of memory.
2. **The secure area.** The result must pass the secure area. It limits wrong tries and holds a key the next step is wrapped with. Phones with a security chip also mix in a secret from that chip (Weaver). The FP6 has none.
3. **Your data.** That opens Android's synthetic password, which opens the file encryption keys of your data.

If the secure area were broken, step 1 would be the only cost left for each guess. So DiamaneOS makes it expensive:

| | Stock Android | DiamaneOS |
|---|---|---|
| scrypt settings | N = 2⁹, r = 8, p = 2 | N = 2¹⁸, r = 8, p = 1 |
| Memory per guess | 512 KiB | 256 MiB |
| Time per unlock on the phone | under 50 ms | about a second |

- **For you:** typing your lock takes about a second longer. Fingerprint unlocks skip this step.
- **For an attacker:** published benchmarks of the same work put a top graphics card at no more than about 100 guesses a second. A million a second takes more than 10,000 such cards.
- **When it applies:** to your lock, from the moment you set or change it. The fingerprint's second-factor PIN keeps Android's setting.

## The generated passphrase

- **Random words.** The phone draws every word on its own, uniformly, with Android's secure random generator.
- **The long list.** EFF's large word list, 7,772 words (the ones made only of a to z), 12.9 bits a word. 5 to 8 words, 6 by default.
- **The short version.** EFF's short word list 2, 1,295 words, 10.3 bits a word. Always 6 words. No two words start with the same 3 letters, so you type only those: 18 letters, no spaces, and nothing is lost.
- **What counts as strong.** A generated passphrase, a generated 20-digit PIN, or a password of 20 or more characters with at least 5 different characters and not only digits. A pattern or a PIN you choose always counts as weaker, whatever its length.
- **Choosing a weaker lock.** Setup first shows a screen that explains the risk. The lock service itself refuses a weaker lock unless that screen was accepted in the last 10 minutes, and each acceptance covers one lock.

## Learning it

For the first 14 days the phone asks for your new lock about once a day: fingerprint stops working 24 hours after you last typed it. Only time with the phone switched on counts. After that, fingerprint works as usual.

## Day to day

- **After every restart** you need the full lock. Fingerprint only works after that first unlock.
- **Fingerprint with a second factor.** You can require a separate PIN on top of your fingerprint.
- **Auto reboot.** After 12 hours without an unlock, the phone restarts and your data is locked away again. Change it under Settings > Security & privacy > Exploit protection > Auto reboot.
- **Nothing left on unencrypted storage.** Android keeps a copy of the lock's check data (its salt, the scrypt settings and the secure area's handle) on an unencrypted partition, for factory reset protection. DiamaneOS does not use that protection and does not write the copy.

See also the [known limitations](/limitations/) of the secure area, and the [features](/features/#fg-lock) of the screen lock.
