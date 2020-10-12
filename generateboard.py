#!/usr/bin/env python

import sys
from threading import Event

import libnochmal


if len(sys.argv) < 2:
    print("Usage: {} <output_board_file> [<seed>]".format(sys.argv[0]))
    sys.exit(1)

seed = None
if len(sys.argv) == 3:
    seed = sys.argv[2]
    libnochmal.set_seed(seed)

board = libnochmal.Board()

# randomly fill the board
# #try:
# #    libnochmal.fill_randomly_smarter(board)
# #except KeyError:
# #    print("Couldn't generate a board for seed '{}'".format(seed))
# #    sys.exit(1)
# #print("Successfully generated a board for seed '{}'!".format(seed))

state = libnochmal.BacktrackingState()

stopFlag = Event()
# thread = PerpetualTimer(stopFlag, lambda: print(board, end="\n\n"), 1.0)
thread = libnochmal.PerpetualTimer(stopFlag, lambda: print("\rlvl. {}, try no. {}".format(state.level, state.tries), end=""), 0.1)
thread.start()

libnochmal.fill_smart(board, state)

# this will stop the timer
stopFlag.set()
print("\nFinal amount of tries: {}, final level: {}".format(state.tries, state.level))

# board = libnochmal.read_board_from_file(sys.argv[1])
libnochmal.distribute_stars(board)

msgs = libnochmal.check_columns(board)
msgs.extend(libnochmal.check_stars_per_color(board))

for msg in msgs:
    print(msg)

print(board)

# write the board to file
boardFileName = sys.argv[1]
libnochmal.write_board_to_file(board, boardFileName)
