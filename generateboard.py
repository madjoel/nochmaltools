#!/usr/bin/env python

import sys
from random import Random
from threading import Event
from datetime import datetime, timedelta

import libnochmal as ln


if len(sys.argv) < 2:
    print("Usage: {} <output_board_file> [<seed as integer>]".format(sys.argv[0]))
    sys.exit(1)

seed = 0
if len(sys.argv) == 3:
    try:
        seed = int(sys.argv[2])
    except ValueError:
        print("Warning: Seed is not an integer, falling back to default value.")
RNG = Random(seed)

board = ln.Board()

state = ln.BacktrackingState()
stopFlag = Event()
thread = ln.PerpetualTimer(stopFlag, lambda: print("\rlvl. {:0>2}, try no. {}".format(state.level, state.tries), end=""), 0.1)
thread.start()

components = ln.create_random_component_order(RNG)

order_str = ['', '']
for i in range(len(components)):
    print("{:0>2}".format(i), end=" ")
    order_str[0] += "{:0>2} ".format(i)
print()
order_str[0] = order_str[0].strip()

for (c, n) in components:
    print("{}{}".format(c.value.upper(), n), end=" ")
    order_str[1] += "{}{} ".format(c.value.upper(), n)
print()
order_str[1] = order_str[1].strip()

started = datetime.now()

# actually generate the board
ln.fill_smart(board, state, components)

finished = datetime.now()

# this will stop the timer
stopFlag.set()
print("\nFinal amount of tries: {}, final level: {}".format(state.tries, state.level))

# board = ln.read_board_from_file(sys.argv[1])
ln.distribute_stars(board, RNG)

# the result
print(board)

# create generated board comment
comment = "This board was generated using nochmaltools generateboard\n" \
          "Generation started:  {}\n" \
          "Generation finished: {}\n" \
          "Duration:            {}\n" \
          "Seed:                {}\n" \
          "Component order:     {}\n" \
          "                     {}\n" \
          "Total tries:         {}".format(started, finished, (finished - started), seed, order_str[0], order_str[1],
                                           state.tries)

# write the board to file
boardFileName = sys.argv[1]
ln.write_board_to_file(board, boardFileName, comment)
