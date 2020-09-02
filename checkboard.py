#!/usr/bin/env python

import sys

import libnochmal


if len(sys.argv) != 2:
    print("Usage: {} <board_file>".format(sys.argv[0]))
    sys.exit(1)

boardFileName = sys.argv[1]
board = libnochmal.read_board_from_file(boardFileName)

if not board:
    print("Board could not be read from file, exiting.")
    sys.exit(2)

print(repr(board))
print()

# now check the board
# - 21 tiles of each color
# - each column contains at least one of each color
# - each column contains exactly one star
# - each color consists of 6 connected components which contain 1, 2, 3, 4, 5 and 6 tiles
# - each color has exactly 3 stars

error_msgs = []

print("Checking color distribution ...", end="", flush=True)
msgs = libnochmal.check_color_distribution(board)
if len(msgs) == 0:
    print(" successful.", flush=True)
else:
    error_msgs.extend(msgs)
    print(" failed.", flush=True)

print("Checking columns ...", end="", flush=True)
msgs = libnochmal.check_columns(board)
if len(msgs) == 0:
    print(" successful.", flush=True)
else:
    error_msgs.extend(msgs)
    print(" failed.", flush=True)

print("Checking color components ...", end="", flush=True)
msgs = libnochmal.check_components(board)
if len(msgs) == 0:
    print(" successful.", flush=True)
else:
    error_msgs.extend(msgs)
    print(" failed.", flush=True)

print("Checking stars per color ...", end="", flush=True)
msgs = libnochmal.check_stars_per_color(board)
if len(msgs) == 0:
    print(" successful.", flush=True)
else:
    error_msgs.extend(msgs)
    print(" failed.", flush=True)

# finally print all accumulated error messages
if len(error_msgs) > 0:
    print("\nError messages:")
    for msg in error_msgs:
        print(msg)
else:
    print("\nOH YEAH! A valid Board!")
