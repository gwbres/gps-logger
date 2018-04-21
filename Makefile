MSPDIR ?= /usr/bin
CC = $(MSPDIR)/msp430-gcc

MCU = msp430g2553

CFLAGS = -0s -Wall -g -mmcu=$(MCU)
CFLAGS += -DLOW_POWER

OBJ = main

RM = rm -rf

$(OBJ): $(OBJ).c
	$(CC) $(CFLAGS) $(OBJ).c -o $(OBJ).elf

clean:
	$(RM) $(OBJ).elf
