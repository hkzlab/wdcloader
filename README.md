# wdcloader - Loader utility for WDC 65xxx devboards

## Introduction

wdcloader is a rewrite in Python of the Java [tool](https://github.com/andrew-jacobs/dev65/blob/master/src/com/wdc65xx/sxb/Uploader.java) by Andrew Jacobs. It also adds support loading arbitrary binary data into memory.

### Disclaimer

I take NO responsibility for what happens if you decide to use this tool. Your computer might crash, catch fire or be destroyed in other nasty ways. Your devboards too!
You're encourauged to take what you deem fit from this, and use it in your projects though!

## Usage

### Build & Install

This tool only runtime dependency is `pyserial`. You can build and install it by running

```
pip install --user .
```

inside the cloned directory.

### Functionality

✅ means I tested the functionality and it works, ❌ means I tested the functionality and found issues, ? means that the functionality has yet to be tested.

* [✅] Detects W65C02SXB
* [✅] Detects W65C816SXB
* [?] Detects W65C165SXB
* [✅] Can read and write RAM in W65C02SXB
* [✅] Can read and write RAM in W65C816SXB
* [?] Can read and write RAM in W65C165SXB
* [?] Can execute memory in any board

## Credits

- [Andrew Jacobs](https://github.com/andrew-jacobs) for the original version of this tool

## Licence

I honor the licence used by the original project this is derived from: [CC BY-SA 4.0 DEED](https://creativecommons.org/licenses/by-sa/4.0/)
