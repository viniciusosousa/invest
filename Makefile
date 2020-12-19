CC = gcc
CFLAGS = -I~/lib/sqlite
CLIB = -L~/lib/sqlite
libs = -lsqlite3
all: invest

all: invest

invest: src/invest.c
	$(CC) -g $(CFLAGS) $(CLIB) $^ $(libs) -o $@
