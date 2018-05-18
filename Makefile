MSPDIR ?= /usr/bin

CC = $(MSPDIR)/msp430-gcc
CXX = $(MSPDIR)/msp430-g++
OBJCOPY = $(MSPDIR)/msp430-objcopy
OBJDUMP = $(MSPDIR)/msp430-objdump

MCU = msp430g2553

CFLAGS = -0s -Wall
CFLAGS += -g -mmcu=$(MCU)

OBJ = main
SRCS = GPS.c

RM = rm -rf

all: flash

$(OBJ).o: $(OBJ).c
	$(CC) $(CFLAGS) $(OBJ).c -o $(OBJ).o $(SRCS)

$(OBJ).hex: $(OBJ).o
	$(OBJCOPY) -O ihex $(OBJ).o $(OBJ).hex

flash: $(OBJ).hex
	@echo "Now use mspdebug to flash $(OBJ).hex with:"
	@echo "# mspdebug rf2500"
	@echo "# erase"
	@echo "# prog $(OBJ).hex"

clean:
	$(RM) *.o *.hex
