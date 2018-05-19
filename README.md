## Mini GPS data logger

The idea behind this project is to have a
long lasting GPS data logger.

The selected module is the PMTK3339 GPS receiver
provided by Adafruits on a breakout board.

An MSP430 is used to kick start the GPS module,
this device has extensive options to reduce power
consumption.

### What you can learn from this project

* How to compile code for MSP430 devices
* Use MSP430 features to reduce power consumption
* 
* Manipulate coordinates
	* D° M' S"
	* Decimal degrees
	* etc.. 
* Discover NMEA data 

### User interface

![alt text](https://github.com/gwbres/gps-logger/blob/master/tests/GUI1.png)

Use the project Wiki to learn how to use the API and
much more.

### Getting started

Required packages:

```bash
# apt-get install binutils-msp430 gcc-msp430 msp430-libc mspdebug
```

compile the program with

```bash
make
```

I use *mspdebug* and an MSP430 launchpad to program my MCUs:

```bash
# mspdebug rf2500
# erase
# prog main.hex
# run
```
