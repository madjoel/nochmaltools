from math import factorial
import random


COLORS_REFERENCE_SET = {'r', 'o', 'y', 'g', 'b'}
COLORS_REFERENCE_LIST = ['r', 'o', 'y', 'g', 'b']
COLOR_UNINITIALIZED = 'w'
OFFSETS = [
    (0, -1),
    (1, 0),
    (0, 1),
    (-1, 0),
]
SOLUTION_COUNTER = 0
RNG = random.Random()


class Tile:
    def __init__(self, color, star=False):
        self._color = color
        self._star = star

    @property
    def color(self):
        return self._color

    @property
    def star(self):
        return self._star

    @star.setter
    def star(self, value):
        self._star = value


class Board:
    def __init__(self, width=15, height=7):
        self._width = width
        self._height = height
        self._tiles = [Tile(COLOR_UNINITIALIZED) for _ in range(width * height)]

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
                    s += tile.color.upper()
                else:
                    s += tile.color

            if y != self._height - 1:
                s += '\n'
        return s

    def __repr__(self):
        s = "{}x{} Board:\n".format(self._width, self._height)
        s += str(self)
        return s


def read_board_from_file(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()
        width = int(lines[0].strip())
        height = int(lines[1].strip())

        board = Board(width, height)

        for i in range(2, len(lines)):
            line = lines[i].strip()
            for j in range(len(line)):
                tile = board.get_tile_at(j, i - 2)
                if line[j].isupper():
                    tile._star = True

                tile._color = line[j].lower()

                if line[j].lower() not in COLORS_REFERENCE_SET | {COLOR_UNINITIALIZED}:
                    print("Unrecognized color '{}' at ({}, {})".format(line[j].lower(), j, i - 2))
                    return None

        return board


def write_board_to_file(board, filename):
    with open(filename, 'w') as file:
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
def check_columns(board, lazy=False):
    error_msgs = []

    for col in range(board.width):
        colors_seen = {
            'r': False,
            'o': False,
            'y': False,
            'g': False,
            'b': False
        }
        stars = 0

        for y in range(board.height):
            colors_seen[board.get_tile_at(col, y).color] = True
            if board.get_tile_at(col, y).star:
                stars += 1

        if stars != 1:
            error_msgs.append("Column {} has {} stars instead of 1".format(col, stars))
            if lazy:
                return error_msgs

        for (k, v) in colors_seen.items():
            if not v:
                error_msgs.append("Column {} is missing the '{}' color".format(col, k))
                if lazy:
                    return error_msgs

    return error_msgs


# checks that each color has a 1-, 2-, 3-, 4-, 5- and 6-component
def check_components(board, lazy=False):
    error_msgs = []

    components = {
        'r': set(),
        'o': set(),
        'y': set(),
        'g': set(),
        'b': set()
    }

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

    star_counts = {
        'r': 0,
        'o': 0,
        'y': 0,
        'g': 0,
        'b': 0
    }

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
            board.set_tile_at(x, y, Tile(RNG.choice(COLORS_REFERENCE_LIST)))


# fill a board a little smarter, but still randomly
# seeds 8, 151, 213 were tested to work, for all seeds to work, this should be done by backtracking
def fill_randomly_smarter(board):
    color_counts = dict(zip(COLORS_REFERENCE_LIST, [0, 0, 0, 0, 0]))
    available_colors = set(COLORS_REFERENCE_LIST)

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


# distribute stars in the board
def distribute_stars(board, assume_no_stars=False):
    if not assume_no_stars:
        for y in range(board.height):
            for x in range(board.width):
                tile = board.get_tile_at(x, y)
                if tile.star:
                    tile.star = False
                    board.set_tile_at(x, y, tile)

    stars_per_color = {
        'r': set(),
        'o': set(),
        'y': set(),
        'g': set(),
        'b': set()
    }

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


# not fully implemented yet
def _component_is_placeable_at(board, color, size, x, y):
    # fail if the first tile of this color can't even be placed
    if not _tile_color_is_placeable_at(board, color, x, y, check_neighbours=True):
        return False

    # fail if there is not enough space for the component to fit
    free_space = board.get_component(x, y)
    if len(free_space) < size:
        return False

    obstructed_space = set()
    for (x, y) in free_space:
        for (ox, oy) in OFFSETS:
            tile = board.get_tile_at(x + ox, y + oy)
            if tile and tile.color == color:
                obstructed_space.add((x, y))

        # check if the column has capacity for more of this color
        if _get_capacity_for_color_in_column(board, color, x) < 1:
            obstructed_space.add((x, y))

    actual_space = free_space - obstructed_space
    possible_component = _get_connected_coords(actual_space, (x, y))[0]
    if len(possible_component) >= size:
        return True  # todo: actually it must still be tested, if a combination exists, that does not block any column

    return False


def _tile_color_is_placeable_at(board, color, x, y, check_neighbours=False, do_not_check_these_coords=None):
    if do_not_check_these_coords is None:
        do_not_check_these_coords = set()

    tile = board.get_tile_at(x, y)

    # fail if already initialized
    if tile.color != COLOR_UNINITIALIZED:
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


def _get_capacity_for_color_in_column(board, color, col):
    colors_seen = set()
    free_in_col = 0
    for row in range(board.height):
        current_color = board.get_tile_at(col, row).color
        if current_color == 'w':
            free_in_col += 1
        else:
            colors_seen.add(current_color)

    amount_of_missing_colors = len(COLORS_REFERENCE_SET) - len(colors_seen)
    capacity = free_in_col - amount_of_missing_colors
    if color not in colors_seen:
        capacity += 1

    return capacity


def _get_possible_colors_for_column(board, col):
    possible_colors = set()
    for c in COLORS_REFERENCE_SET:
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


# calculates the amount of unique combinations of size r in a collection of n elements
# itertools.combinations([1, 2, ... , n], r) yields all of those combinations
def _calc_amount_of_combination(n, r):
    return factorial(n) / factorial(r) / factorial(n-r)