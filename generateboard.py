#!/usr/bin/env python

import sys
from threading import Event

import libnochmal as ln


if len(sys.argv) < 2:
    print("Usage: {} <output_board_file> [<seed>]".format(sys.argv[0]))
    sys.exit(1)

seed = None
if len(sys.argv) == 3:
    seed = sys.argv[2]
    ln.set_seed(seed)

board = ln.Board()

state = ln.BacktrackingState()
stopFlag = Event()
thread = ln.PerpetualTimer(stopFlag, lambda: print("\rlvl. {:0>2}, try no. {}".format(state.level, state.tries), end=""), 0.1)
thread.start()

# actually generate the board
ln.fill_smart(board, state)

# this will stop the timer
stopFlag.set()
print("\nFinal amount of tries: {}, final level: {}".format(state.tries, state.level))

# board = ln.read_board_from_file(sys.argv[1])
ln.distribute_stars(board)

# the result
print(board)

# write the board to file
boardFileName = sys.argv[1]
ln.write_board_to_file(board, boardFileName)
