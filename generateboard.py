#!/usr/bin/env python

import sys
from random import Random
from threading import Event
from datetime import datetime
import signal
import argparse
from typing import List, Tuple

import libnochmal as ln


ARGS: argparse.Namespace
BOARD = ln.Board()
STATE = ln.BacktrackingState()
ORDER = ['', '']
STARTED: datetime
FINISHED: datetime


def main():
    global ARGS, ORDER, STARTED, FINISHED

    cli_parser = argparse.ArgumentParser(description='Generate a board for the game "Noch mal!".')
    cli_parser.add_argument('-s', '--seed', type=int, default=0, metavar='<seed_as_integer>',
                            help='The seed used for the generation of this board')
    cli_parser.add_argument('-l', '--limit-free-space', type=int, default=32, choices=range(1, 105),
                            metavar='<limit_as_integer>',
                            help='With this setting the choices for the next component to be placed at will be limited '
                                 'to the first <limit_as_integer> free spaces')
    cli_parser.add_argument('-p', '--write-pngs', action='store_true',
                            help='Write every placement step to a png file (Requires PyPNG to be installed) (WARNING: '
                                 'can create huge amount of files!)')
    cli_parser.add_argument('--line6', action='store_true',
                            help='This deactivates the line6-constraint and allows components of size 6 to be placed '
                                 'in a horizontal line')
    cli_parser.add_argument('--multiple-comp-per-col', action='store_true',
                            help='This deactivates the only-one-color-component-per-column-constraint and allows '
                                 'multiple components of the same color to be present in one column')
    cli_parser.add_argument('--order', type=str, default='RFCI', choices=['RFCI', 'RAND', 'DESC'],
                            help='This controls the order in which the components are placed on the board.\n  RFCI: '
                                 'Random with fixed color interval. RAND: completely random. DESC: Ordered from big to '
                                 'small component size with default color order. (default is RFCI)')
    cli_parser.add_argument('outfile', help='The file name to save the generated board to')
    ARGS = cli_parser.parse_args()

    # set the signal handlers
    signal.signal(signal.SIGINT, conclude_generation)
    signal.signal(signal.SIGUSR1, print_board)

    rng = Random(ARGS.seed)

    # setup timer to print status
    stop_flag = Event()
    thread = ln.PerpetualTimer(stop_flag, lambda: print("\relapsed time: {}, lvl. {:0>2}, placement no. {}"
                                                        .format((datetime.now() - STARTED), STATE.level,
                                                                STATE.placements), end=""), 0.1)
    thread.start()

    components: List[Tuple[ln.Color, int]]
    if ARGS.order == 'DESC':
        components = ln.create_descending_component_order()
    elif ARGS.order == 'RFCI':
        components = ln.create_random_fixed_color_interval_component_order(rng)
    else:
        components = ln.create_descending_component_order()
        rng.shuffle(components)

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

    STARTED = datetime.now()

    # actually generate the board
    success = ln.fill_smart(BOARD, STATE, components, write_pngs=ARGS.write_pngs,
                            free_space_limit=ARGS.limit_free_space, no_line6=(not ARGS.line6),
                            only_one_comp_per_col=(not ARGS.multiple_comp_per_col))
    if not success:
        print("\nFailed to generate a board with seed {}.".format(ARGS.seed))
    else:
        ln.distribute_stars(BOARD, rng)

    # this will stop the timer
    stop_flag.set()
    thread.join()

    conclude_generation(-1, None)


def conclude_generation(signum, frame):
    global FINISHED
    FINISHED = datetime.now()

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
              "Comp. order setting: {}\n" \
              "Free space limit:    {}\n" \
              "line6-constraint:    {}\n" \
              "mul-comp-constraint: {}\n" \
              "Total placements:    {}\n" \
              "Final level:         {}".format(STARTED, "aborted:  " if aborted else "finished: ", FINISHED,
                                               (FINISHED - STARTED), ARGS.seed, ORDER[0], ORDER[1], ARGS.order,
                                               ARGS.limit_free_space,
                                               "DEACTIVATED" if ARGS.line6 else "ACTIVATED",
                                               "DEACTIVATED" if ARGS.multiple_comp_per_col else "ACTIVATED",
                                               STATE.placements, STATE.level)

    # write the board to file
    ln.write_board_to_file(BOARD, ARGS.outfile, comment)

    sys.exit(1)


def print_board(signum, frame):
    print("\n\nIntermediary result after {}: placements: {}, level: {}"
          .format(datetime.now() - STARTED, STATE.placements, STATE.level))
    print(BOARD)
    print()


if __name__ == "__main__":
    main()
