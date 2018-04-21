# Portable GPS data logger using MSP430 by TI

# Getting started

```bash
# apt-get install binutils-msp430 gcc-msp430 msp430-libc mspdebug
```

compile the application with

```bash
make
```

# Flash the program onto MSP430x

flash with
```bash
# mspdebug rf2500
# erase
# load main.elf
# run
```

# tools.py

A python tool to control the PMKT module over
serial port. Requires "pyserial".
