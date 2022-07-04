import random
from enum import Enum
from math import factorial
from threading import Thread

from typing import Tuple, List

OFFSETS = [
    (0, -1),
    (1, 0),
    (0, 1),
    (-1, 0),
]
SOLUTION_COUNTER = 0
RNG = random.Random()

DEFAULT_BOARD_WIDTH = 15
DEFAULT_BOARD_HEIGHT = 7

POINTS_PER_COLUMN = [5, 3, 3, 3, 2, 2, 2, 1, 2, 2, 2, 3, 3, 3, 5]


class Color(Enum):
    RED = 'r'
    ORANGE = 'o'
    YELLOW = 'y'
    GREEN = 'g'
    BLUE = 'b'
    WHITE = '_'
    UNINITIALIZED = '_'

    def to_rgb(self):
        if self == Color.RED: return "#FA0046"
        if self == Color.ORANGE: return "#FA8200"
        if self == Color.YELLOW: return "#FADC00"
        if self == Color.GREEN: return "#96BE1E"
        if self == Color.BLUE: return "#5AC8FA"
        if self == Color.WHITE: return "#FFFFFF"
        else:
            return "FF00FF"

    def to_rgb_secondary(self):
        if self == Color.RED: return '#FB5986'
        if self == Color.ORANGE: return '#FBAD59'
        if self == Color.YELLOW: return '#FBE859'
        if self == Color.GREEN: return '#BAD46C'
        if self == Color.BLUE: return '#93DBFB'
        if self == Color.WHITE: return '#ECECEC'
        else:
            return "FF77FF"

    @classmethod
    def ref_set(cls, with_white=False):
        if with_white:
            return {Color.RED, Color.ORANGE, Color.YELLOW, Color.GREEN, Color.BLUE, Color.WHITE}
        else:
            return {Color.RED, Color.ORANGE, Color.YELLOW, Color.GREEN, Color.BLUE}

    @classmethod
    def ref_list(cls, with_white=False):
        if with_white:
            return [Color.RED, Color.ORANGE, Color.YELLOW, Color.GREEN, Color.BLUE, Color.WHITE]
        else:
            return [Color.RED, Color.ORANGE, Color.YELLOW, Color.GREEN, Color.BLUE]

    def __lt__(self, other):
        return self.value < other.value


class Tile:
    def __init__(self, color=Color.UNINITIALIZED, star=False):
        self._color = color
        self._star = star

    @property
    def color(self):
        return self._color

    @property
    def star(self):
        return self._star

    @color.setter
    def color(self, value):
        self._color = value

    @star.setter
    def star(self, value):
        self._star = value


class Board:
    def __init__(self, width=DEFAULT_BOARD_WIDTH, height=DEFAULT_BOARD_HEIGHT):
        self._width = width
        self._height = height
        self._tiles = [Tile() for _ in range(width * height)]

    @property
    def tiles(self):
        return self._tiles

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    def get_tile_at(self, x, y):
        if self.in_bounds(x, y):
            return self._tiles[self._to_index(x, y)]
        else:
            return None

    def set_tile_at(self, x, y, tile):
        if self.in_bounds(x, y):
            self._tiles[self._to_index(x, y)] = tile

    def get_color_at(self, x, y):
        if self.in_bounds(x, y):
            return self._tiles[self._to_index(x, y)].color

    def set_color_at(self, x, y, color):
        if self.in_bounds(x, y):
            self._tiles[self._to_index(x, y)].color = color

    def get_star_at(self, x, y):
        if self.in_bounds(x, y):
            return self._tiles[self._to_index(x, y)].star

    def set_star_at(self, x, y, value=True):
        if self.in_bounds(x, y):
            self._tiles[self._to_index(x, y)].star = value

    def in_bounds(self, x, y):
        return 0 <= x < self._width and 0 <= y < self._height \
               and self._to_index(x, y) < self._width * self._height

    def _to_index(self, x, y):
        return x + y * self._width

    def get_component(self, x, y):
        tile = self.get_tile_at(x, y)
        c = tile.color

        tiles_in_component = {(x, y)}
        tiles_to_check = [(x, y)]

        while len(tiles_to_check) > 0:
            (cx, cy) = tiles_to_check.pop()

            for (ox, oy) in OFFSETS:
                neighbour_coords = (cx + ox, cy + oy)
                neighbour_tile = self.get_tile_at(neighbour_coords[0], neighbour_coords[1])
                if neighbour_tile and neighbour_tile.color == c:
                    if neighbour_coords not in tiles_in_component:
                        tiles_to_check.append(neighbour_coords)
                        tiles_in_component.add(neighbour_coords)

        return tiles_in_component

    def __str__(self):
        s = ""
        for y in range(self._height):
            for x in range(self._width):
                tile = self.get_tile_at(x, y)
                if tile.star:
                    s += tile.color.value.upper()
                else:
                    s += tile.color.value

            if y != self._height - 1:
                s += '\n'
        return s

    def __repr__(self):
        s = "{}x{} Board:\n".format(self._width, self._height)
        s += str(self)
        return s


class PerpetualTimer(Thread):
    def __init__(self, event, fn, interval):
        Thread.__init__(self)
        self.stopped = event
        self.fn = fn
        self.interval = interval
        self.daemon = True

    def run(self):
        while not self.stopped.wait(self.interval):
            self.fn()


class BacktrackingState:
    def __init__(self):
        self.level = 0
        self.tries = 0

    def inc_level(self):
        self.level += 1

    def dec_level(self):
        self.level -= 1

    def inc_tries(self):
        self.tries += 1


def read_board_from_file(filename):
    with open(filename, 'r') as file:
        lines = []
        for line in file.readlines():
            if line.strip().startswith('#'):
                continue
            lines.append(line)

        width = int(lines[0].strip())
        height = int(lines[1].strip())

        board = Board(width, height)

        for i in range(2, len(lines)):
            line = lines[i].strip()
            for j in range(len(line)):
                tile = board.get_tile_at(j, i - 2)
                if line[j].isupper():
                    tile._star = True

                try:
                    tile._color = Color(line[j].lower())
                except ValueError:
                    print("Unrecognized color '{}' at ({}, {})".format(line[j].lower(), j, i - 2))
                    return None

        return board


def write_board_to_file(board: Board, filename, comment: str = ''):
    with open(filename, 'w') as file:
        comment_lines = []
        for cline in comment.splitlines(False):
            comment_lines.append("# {}\n".format(cline))
        file.writelines(comment_lines)

        lines = ["{}\n".format(board.width), "{}\n".format(board.height)]
        lines.extend(str(board).splitlines(True))
        file.writelines(lines)


# --- checking functions ---

# checks if there is a missing color or wrong amount of tiles per color
def check_color_distribution(board, lazy=False):
    error_msgs = []
    amounts = dict()

    for tile in board.tiles:
        if tile.color not in amounts:
            amounts[tile.color] = 1
        else:
            amounts[tile.color] += 1

    if len(amounts.items()) != 5:
        error_msgs.append("The board is missing {} color(s)".format(5 - len(amounts.items())))
        if lazy:
            return error_msgs

    for (k, v) in amounts.items():
        if v != 21:
            error_msgs.append("The color '{}' has {} tiles instead of 21".format(k, v))
            if lazy:
                return error_msgs

    return error_msgs


# checks if all columns have one star and at least one tile of every color
# also checks that all occurrences of a color are connected
def check_columns(board, lazy=False):
    error_msgs = []

    for col in range(board.width):
        colors_seen = dict(zip(Color.ref_list(), [-1 for _ in range(len(Color.ref_list()))]))
        last_color: Color = Color.UNINITIALIZED
        stars = 0

        for y in range(board.height):
            current_color: Color = board.get_tile_at(col, y).color
            if colors_seen[current_color] == -1:
                colors_seen[current_color] = y
            else:
                if current_color == last_color or \
                        (col, colors_seen[current_color]) in get_component_coords(board, col, y):  # fine
                    pass
                else:  # not fine
                    error_msgs.append("Column {} has multiple occurrences of color {} at row {}"
                                      .format(col, current_color, y))
                    if lazy:
                        return error_msgs

            if board.get_tile_at(col, y).star:
                stars += 1

            last_color = current_color

        if stars != 1:
            error_msgs.append("Column {} has {} stars instead of 1".format(col, stars))
            if lazy:
                return error_msgs

        for (k, v) in colors_seen.items():
            if v == -1:
                error_msgs.append("Column {} is missing the '{}' color".format(col, k))
                if lazy:
                    return error_msgs

    return error_msgs


# checks that each color has a 1-, 2-, 3-, 4-, 5- and 6-component
def check_components(board, lazy=False):
    error_msgs = []

    components = dict(zip(Color.ref_list(), [set() for _ in range(len(Color.ref_list()))]))
    visited_coords = set()

    for y in range(board.height):
        for x in range(board.width):
            if (x, y) in visited_coords:
                continue
            else:
                comp = board.get_component(x, y)
                visited_coords.update(comp)

                if len(comp) > 6:
                    error_msgs.append("The component at {} is too large ({} tiles)".format(comp, len(comp)))
                    if lazy:
                        return error_msgs

                color = board.get_tile_at(x, y).color
                if len(comp) not in components[color]:
                    components[color].add(len(comp))
                else:
                    error_msgs.append("A component of {} tiles already exists for color '{}'".format(len(comp), color))
                    if lazy:
                        return error_msgs

    reference = {1, 2, 3, 4, 5, 6}
    for (k, v) in components.items():
        if v != reference:
            missing = reference - v
            toomuch = v - reference
            if len(missing) > 0:
                error_msgs.append("The color '{}' is missing the components with {} tiles".format(k, missing))
                if lazy:
                    return error_msgs
            if len(toomuch) > 0:
                error_msgs.append("The color '{}' has components with {} tiles that are not allowed".format(k, toomuch))
                if lazy:
                    return error_msgs

    return error_msgs


# checks that every color has exactly 3 stars
def check_stars_per_color(board, lazy=False):
    error_msgs = []

    star_counts = dict(zip(Color.ref_list(), [0 for _ in range(len(Color.ref_list()))]))

    for tile in board.tiles:
        if tile.star:
            if tile.color not in star_counts:
                star_counts[tile.color] = 1
            else:
                star_counts[tile.color] += 1

    for (k, v) in star_counts.items():
        if v != 3:
            error_msgs.append("The color '{}' has {} star(s) instead of 3".format(k, v))
            if lazy:
                return error_msgs

    return error_msgs


# performs all checks in a single function, if lazy returns on first error
def check_all(board, lazy=False):
    error_msgs = check_color_distribution(board, lazy)
    if lazy and len(error_msgs) != 0:
        return error_msgs

    error_msgs.extend(check_stars_per_color(board, lazy))
    if lazy and len(error_msgs) != 0:
        return error_msgs

    error_msgs.extend(check_columns(board, lazy))
    if lazy and len(error_msgs) != 0:
        return error_msgs

    error_msgs.extend(check_components(board, lazy))
    return error_msgs


# --- generation functions ---

def set_seed(seed):
    RNG.seed(seed)


# fill a board completely at random
def fill_randomly(board):
    for y in range(board.height):
        for x in range(board.width):
            board.set_tile_at(x, y, Tile(RNG.choice(Color.ref_list())))


# fill a board a little smarter, but still randomly
# seeds 8, 151, 213 were tested to work, for all seeds to work, this should be done by backtracking
def fill_randomly_smarter(board):
    color_counts = dict(zip(Color.ref_list(), [0 for _ in range(len(Color.ref_list()))]))
    available_colors = Color.ref_set()

    for x in range(board.width):
        for y in range(board.height):
            possible_colors = list(available_colors.intersection(_get_possible_colors_for_column(board, x)))
            possible_colors.sort()
            if len(possible_colors) < 1:
                print("FATAL: Ran out of valid colors for tile {}, {} - returning prematurely.".format(x, y))

            c = RNG.choice(possible_colors)
            board.set_tile_at(x, y, Tile(c))
            color_counts[c] += 1
            if color_counts[c] == 21:
                available_colors.remove(c)


def fill_smart(board, state):
    # components = [(c, n) for n in range(6, 0, -1) for c in Color.ref_list()]
    components_order = dict(zip(Color.ref_list(), [list(range(6, 0, -1)) for _ in range(6)]))

    color_order = Color.ref_list()
    RNG.shuffle(color_order)

    for c in color_order:
        RNG.shuffle(components_order[c])

    components = list()
    for component_index in range(6):
        for color_index in range(len(color_order)):
            components.append((color_order[color_index], components_order[color_order[color_index]][component_index]))

    for i in range(len(components)):
        print("{:0>2}".format(i), end=" ")
    print()

    for (c, n) in components:
        print("{}{}".format(c.value.upper(), n), end=" ")
    print()

    _fill_smart_backtrack(board, components, 0, state)


def _fill_smart_backtrack(board, components, comp_index, state):
    if comp_index == 5 * 6:
        return True  # done

    component_color = components[comp_index][0]
    component_size = components[comp_index][1]

    free_space = _get_free_tiles(board)
    for (fx, fy) in free_space:
        free_space_component = _get_connected_coords(free_space, (fx, fy))[0]
        combinations = get_all_graphs_of_size(free_space_component, (fx, fy), component_size)
        for combi in combinations:
            if _combination_is_placeable(board, combi, component_color, free_space):
                # place combination
                for (x, y) in combi:
                    board.set_tile_at(x, y, Tile(component_color))
                state.inc_tries()

                # continue with next component
                state.inc_level()
                if _fill_smart_backtrack(board, components, comp_index + 1, state):
                    # print('Placing component index {} ...'.format(comp_index + 1))
                    return True
                else:
                    for (x, y) in combi:
                        board.set_tile_at(x, y, Tile())

    state.dec_level()
    return False


def _combination_is_placeable(board, combination, color, free_space):
    result = True

    # line6-constraint
    # to avoid having 6 tiles of the same color in a row this constraint is applied
    if len(combination) == 6:
        _, first_y = list(combination)[0]
        all_the_same = True

        for (_, y) in combination:
            if first_y != y:
                all_the_same = False
                break

        if all_the_same:
            return False

    for (x, y) in combination:
        if _tile_color_is_placeable_at(board, color, x, y, True, combination):
            board.set_tile_at(x, y, Tile(color))
        else:
            result = False
            break

    if result:
        # check if combination separates free space into multiple components
        for coord in combination:
            if coord in free_space:
                free_space.remove(coord)

        if len(_get_connected_coords(free_space)) > 1:
            result = False

    # remove combination
    for (x, y) in combination:
        board.set_tile_at(x, y, Tile())

    return result


def _get_free_tiles(board):
    free_tiles = []

    for x in range(15):
        for y in range(7):
            if board.get_tile_at(x, y).color == Color.UNINITIALIZED:
                free_tiles.append((x, y))

    return free_tiles


# distribute stars in the board
def distribute_stars(board, assume_no_stars=False):
    if not assume_no_stars:
        for y in range(board.height):
            for x in range(board.width):
                tile = board.get_tile_at(x, y)
                if tile.star:
                    tile.star = False
                    board.set_tile_at(x, y, tile)

    stars_per_color = dict(zip(Color.ref_list(), [set() for _ in range(len(Color.ref_list()))]))
    _place_stars_backtrack(board, stars_per_color, 0)


def _star_is_placeable_at(board, stars_per_color, x, y):
    tile = board.get_tile_at(x, y)
    color = tile.color

    # check amount of stars for this color
    if len(stars_per_color[color]) >= 3:
        return False

    # check component for star
    for (cx, cy) in board.get_component(x, y):
        ctile = board.get_tile_at(cx, cy)
        if ctile and ctile.star:
            return False

    return True


def _place_stars_backtrack(board, stars_per_color, col):
    if col == board.width:
        return True  # done

    row_indices = [i for i in range(board.height)]
    RNG.shuffle(row_indices)
    for row in row_indices:
        if _star_is_placeable_at(board, stars_per_color, col, row):
            board.set_star_at(col, row)
            stars_per_color[board.get_tile_at(col, row).color].add((col, row))

            if _place_stars_backtrack(board, stars_per_color, col + 1):
                return True
            else:
                board.set_star_at(col, row, False)
                stars_per_color[board.get_tile_at(col, row).color].remove((col, row))

    return False


def _tile_color_is_placeable_at(board, color, x, y, check_neighbours=False, do_not_check_these_coords=None):
    if do_not_check_these_coords is None:
        do_not_check_these_coords = set()

    tile = board.get_tile_at(x, y)

    # fail if already initialized
    if tile.color != Color.UNINITIALIZED:
        return False

    # fail if a neighbour already has this color
    if check_neighbours:
        for (ox, oy) in OFFSETS:
            xox = x + ox
            yoy = y + oy
            if (xox, yoy) in do_not_check_these_coords:
                continue

            tile = board.get_tile_at(xox, yoy)
            if tile and tile.color == color:
                return False

    # fail if there is not enough capacity in the column for this color
    if _get_capacity_for_color_in_column(board, color, x) < 1:
        return False

    # only-one-color-component-per-column-constraint
    # fail if there is already a tile of this color in this column which is not of the current component
    for col in range(7):
        tile = board.get_tile_at(x, col)
        if tile and tile.color == color and not (x, col) in do_not_check_these_coords:
            return False

    return True


def _get_capacity_for_color_in_column(board, color, col):
    colors_seen = set()
    free_in_col = 0
    for row in range(board.height):
        current_color = board.get_tile_at(col, row).color
        if current_color == Color.UNINITIALIZED:
            free_in_col += 1
        else:
            colors_seen.add(current_color)

    amount_of_missing_colors = len(Color.ref_set()) - len(colors_seen)
    capacity = free_in_col - amount_of_missing_colors
    if color not in colors_seen:
        capacity += 1

    return capacity


def _get_possible_colors_for_column(board, col):
    possible_colors = set()
    for c in Color.ref_set():
        if _get_capacity_for_color_in_column(board, c, col) > 0:
            possible_colors.add(c)
    return possible_colors


# given a set of grid coordinates this function returns every set of coords, that are connected
# if anchor is given, then only returns the set of connected coords that include anchor
def _get_connected_coords(coordinates, anchor=None):
    if anchor and anchor not in coordinates:
        return [[]]

    coords = list(coordinates)
    components = []

    while len(coords) > 0:
        if anchor:
            current_start_coord = anchor
        else:
            current_start_coord = coords.pop()

        reached = {current_start_coord}
        tiles_to_check = [current_start_coord]

        while len(tiles_to_check) > 0:
            (x, y) = tiles_to_check.pop()

            for (ox, oy) in OFFSETS:
                neighbour = (x + ox, y + oy)
                if neighbour in coordinates and neighbour not in reached:
                    tiles_to_check.append(neighbour)
                    reached.add(neighbour)
                    coords.remove(neighbour)
        if anchor:
            return [list(reached)]
        else:
            components.append(list(reached))

    return components


# returns the set of all subgraphs with size amount of nodes given a graph and a start node
def get_all_graphs_of_size(coords, start, size):
    solutions = []  # this will have sets of frozensets as elements

    for i in range(size):
        if i == 0:
            solutions.append({frozenset((start,))})
            if size == 1:
                return solutions[0]
            else:
                continue
        else:
            solutions.append(set())

        # here every subgraph found in the previous solution set is processed
        for subgraph in solutions[i - 1]:  # subgraph is a set of nodes
            # get all possible neighbours of this subgraph
            neighbours = set()
            for node in subgraph:
                neighbours.update(get_neighbours(node, coords))

            # remove the nodes from the subgraph from the set of all possible neighbours
            neighbours = neighbours - subgraph

            # add each combination of the subgraph and one of the found neighbours into the set of new solutions
            for true_neighbour in neighbours:
                new_subgraph = subgraph | {true_neighbour}
                solutions[i].add(frozenset(new_subgraph))

    return solutions[-1]


# gets all neighbours of a coordinate.
# if a set of possible coords is given, only neighbours included in that set are returned
def get_neighbours(coord, coords=None):
    neighbours = []
    x, y = coord
    for (ox, oy) in OFFSETS:
        neighbour = (x + ox, y + oy)
        if coords and neighbour not in coords:
            continue
        neighbours.append(neighbour)
    return neighbours


def get_component_coords(board: Board, x: int, y: int) -> List[Tuple[int, int]]:
    result = [(x, y)]
    color = board.get_tile_at(x, y).color

    queue = [(x, y)]
    while len(queue) > 0:
        coord = queue.pop(0)
        for (nx, ny) in get_neighbours(coord):
            if board.in_bounds(nx, ny) and (nx, ny) not in result and board.get_color_at(nx, ny) == color:
                queue.append((nx, ny))
                result.append((nx, ny))

    return result


# calculates the amount of unique combinations of size r in a collection of n elements
# itertools.combinations([1, 2, ... , n], r) yields all of those combinations
def _calc_amount_of_combination(n, r):
    return factorial(n) / factorial(r) / factorial(n - r)
