#!/usr/bin/env python

import sys
from random import Random
from threading import Event
from datetime import datetime
import signal

import libnochmal as ln


SEED = 0
BOARD = ln.Board()
STATE = ln.BacktrackingState()
FILENAME = ""
ORDER = ['', '']
STARTED: datetime


def main():
    signal.signal(signal.SIGINT, conclude_generation)

    if len(sys.argv) < 2:
        print("Usage: {} <output_board_file> [<seed as integer>]".format(sys.argv[0]))
        sys.exit(1)

    global FILENAME
    FILENAME = sys.argv[1]

    global SEED
    if len(sys.argv) == 3:
        try:
            SEED = int(sys.argv[2])
        except ValueError:
            print("Warning: Seed is not an integer, falling back to default value.")
    rng = Random(SEED)

    stop_flag = Event()
    thread = ln.PerpetualTimer(stop_flag, lambda: print("\rlvl. {:0>2}, placement no. {}"
                                                        .format(STATE.level, STATE.placements), end=""), 0.1)
    thread.start()

    # components = ln.create_random_component_order(rng)
    components = ln.create_descending_component_order()

    global ORDER
    ORDER = ['', '']
    for i in range(len(components)):
        print("{:0>2}".format(i), end=" ")
        ORDER[0] += "{:0>2} ".format(i)
    print()
    ORDER[0] = ORDER[0].strip()

    for (c, n) in components:
        print("{}{}".format(c.value.upper(), n), end=" ")
        ORDER[1] += "{}{} ".format(c.value.upper(), n)
    print()
    ORDER[1] = ORDER[1].strip()

    global STARTED
    STARTED = datetime.now()

    # actually generate the board
    ln.fill_smart(BOARD, STATE, components)

    # this will stop the timer
    stop_flag.set()

    # board = ln.read_board_from_file(sys.argv[1])
    ln.distribute_stars(BOARD, rng)

    conclude_generation(-1, None)


def conclude_generation(signum, frame):
    finished = datetime.now()

    # the result
    print("\nFinal amount of placements: {}, final level: {}".format(STATE.placements, STATE.level))
    print(BOARD)

    aborted = False
    if signum != -1:
        aborted = True

    # create generated board comment
    comment = "This board was generated using nochmaltools generateboard\n" \
              "Generation started:  {}\n" \
              "Generation {}{}\n" \
              "Duration:            {}\n" \
              "Seed:                {}\n" \
              "Component order:     {}\n" \
              "                     {}\n" \
              "Total placements:    {}\n" \
              "Final level:         {}".format(STARTED, "aborted:  " if aborted else "finished: ", finished,
                                               (finished - STARTED), SEED, ORDER[0], ORDER[1], STATE.placements,
                                               STATE.level)

    # write the board to file
    ln.write_board_to_file(BOARD, FILENAME, comment)

    sys.exit(1)


if __name__ == "__main__":
    main()
