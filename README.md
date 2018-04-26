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
serial port and manipulate .nmea data.

```bash
python3 tools.py --help
```

The script can send known commands to the module
over serial port.

```bash
python3 tools.py /dev/ttyUSB0 --status
python3 tools.py /dev/ttyUSB0 --start-logging
```

The script can convert .nmea files to .kml & .gpx
files (kml: Google earth.., gpx: OpenStreetMap, GPSVisualizer..).

```bash
python3 tools.py /dev/ttyUSB0 --nmea-to-kml
python3 tools.py /dev/ttyUSB0 --nmea-to-gpx
```

The script allows to view data waypoints contained
in a .nmea, a .kml or a .gpx file over a map, using
the "geoplotlib" package.

```bash
python3 tools.py /dev/ttyUSB0 --view-coordinates
```

Required python packages to run the script:

1. pyserial
2. geoplotlib <https://github.com/andrea-cuttone/geoplotlib>
