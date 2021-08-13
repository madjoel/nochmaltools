#!/usr/bin/env python3

import os
import random
import time

import tkinter as tk
import tkinter.messagebox as msgbox
from tkinter import ttk
import tkinter.filedialog as tkfd
from PIL import Image, ImageTk

import libnochmal as ln
from libnochmal import Color


class ColorButton(tk.Button):
    def __init__(self, master, color, x, y):
        super(ColorButton, self).__init__(master, bg=color.to_rgb(), activebackground=color.to_rgb_secondary(),
                                          font='TkFixedFont', relief="flat", overrelief="flat")
        self.x = x
        self.y = y
        self.application = master
        self.color = color
        self.star = False
        self.crossed = False
        self['image'] = Application.CIRCLE_IMAGE

    def set_by_tile(self, tile):
        self.set_color(tile.color)

        self.star = tile.star
        if self.star:
            self['image'] = Application.STAR_IMAGE

    def set_color(self, color):
        self.color = color
        self.config(bg=color.to_rgb(), activebackground=color.to_rgb_secondary())

    def click(self, _event):
        if not self.application.check_click(self.x, self.y):
            return

        if self.crossed:
            if self.star:
                self['image'] = Application.STAR_IMAGE
            else:
                self['image'] = Application.CIRCLE_IMAGE
        else:
            self['image'] = Application.CROSS_GRAY_IMAGE

        self.crossed = not self.crossed

    def commit(self):
        self['image'] = Application.CROSS_IMAGE


class SinglePlayerGameState:
    def __init__(self):
        self.board = None
        self.joker_count = 8
        self.toss_counter = 0
        self.tossed = False
        self.started = False
        self.rolled_numbers = [-1, -1]
        self.rolled_colors = [Color.UNINITIALIZED, Color.UNINITIALIZED]
        self.crossed_tiles = []
        self.crossed_tiles_to_commit = []
        self.stars_crossed = 0
        self.columns_crossed = []
        self.colors_crossed = dict(zip(Color.ref_list(), [0 for _ in range(len(Color.ref_list()))]))

    def start(self):
        self.started = True
        self.columns_crossed = [0 for _ in range(self.board.width)]

    def finish(self):
        self.started = False

    def inc_toss_count(self):
        if not self.started or self.tossed:
            return

        self.toss_counter += 1
        self.tossed = True

    def use_joker(self, n=1) -> bool:
        if self.joker_count < n:
            return False
        else:
            self.joker_count -= n
            return True


class Application(tk.Frame):
    STAR_IMAGE = None
    CIRCLE_IMAGE = None
    CROSS_IMAGE = None
    CROSS_GRAY_IMAGE = None
    O_IMAGE = None

    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.grid()

        self.game_state = SinglePlayerGameState()

        # load star and circle image
        script_path = os.path.dirname(os.path.realpath(__file__))
        Application.STAR_IMAGE = ImageTk.PhotoImage(Image.open(script_path + '/img/star.png'))
        Application.CIRCLE_IMAGE = ImageTk.PhotoImage(Image.open(script_path + '/img/circle.png'))
        Application.CROSS_IMAGE = ImageTk.PhotoImage(Image.open(script_path + '/img/cross.png'))
        Application.CROSS_GRAY_IMAGE = ImageTk.PhotoImage(Image.open(script_path + '/img/cross-gray.png'))
        Application.O_IMAGE = ImageTk.PhotoImage(Image.open(script_path + '/img/o.png'))

        # top buttons
        self.load_board_btn = tk.Button(self, text='Open Board')
        self.load_board_btn.grid(row=0, column=0, columnspan=4, sticky='W')
        self.load_board_btn.bind("<Button-1>", self.open_board)

        self.start_game_btn = tk.Button(self, text='Start Game')
        self.start_game_btn.grid(row=0, column=4, columnspan=4)
        self.start_game_btn.bind("<Button-1>", self.start_game)

        self.progress_var = tk.IntVar(self, value=0)
        self.progressbar = ttk.Progressbar(self, maximum=30, variable=self.progress_var)
        self.progressbar.grid(row=0, column=10, columnspan=4, sticky='E')

        # top Letters
        for x in range(ln.DEFAULT_BOARD_WIDTH):
            lbl = tk.Label(self, text=chr(65 + x))
            if x == 7:
                lbl['fg'] = 'red'
            lbl.grid(row=1, column=x)

        # board buttons
        self.board_buttons = []
        for x in range(ln.DEFAULT_BOARD_WIDTH):
            self.board_buttons.append([])
            for y in range(ln.DEFAULT_BOARD_HEIGHT):
                btn = ColorButton(self, Color.UNINITIALIZED, x, y)
                btn.bind("<Button-1>", btn.click)
                btn.grid(row=(y + 2), column=x)
                self.board_buttons[x].append(btn)

        # bottom points per column
        self.board_column_point_labels = []
        for x in range(ln.DEFAULT_BOARD_WIDTH):
            lbl = tk.Label(self, text=ln.POINTS_PER_COLUMN[x])
            lbl.grid(row=9, column=x)
            if x == 7:
                lbl['fg'] = 'red'
            self.board_column_point_labels.append(lbl)

        # bottom buttons
        self.color_dice_1 = ColorButton(self, Color.UNINITIALIZED, -1, -1)
        self.color_dice_1.grid(row=10, column=4)
        self.color_dice_2 = ColorButton(self, Color.UNINITIALIZED, -1, -1)
        self.color_dice_2.grid(row=10, column=5)
        self.number_dice_1 = tk.Label(self, text='0')
        self.number_dice_1.grid(row=10, column=6)
        self.number_dice_2 = tk.Label(self, text='0')
        self.number_dice_2.grid(row=10, column=7)

        self.commit_btn = tk.Button(self, text='Commit')
        self.commit_btn.grid(row=10, column=8, columnspan=3, sticky='W')
        self.commit_btn.bind("<Button-1>", self.commit)

        # status bar
        self.sep = tk.Label(self, text='_______________________________________________________________')
        self.sep.grid(row=11, column=0, columnspan=15)
        self.statusbar = tk.Label(self, text='status bar text here')
        self.statusbar.grid(row=12, column=0, columnspan=15, sticky='W')

    def open_board(self, _event):
        if self.game_state.started:
            pass  # todo: ask if should clear

        f = tkfd.askopenfilename(defaultextension='.dat')
        if len(f) == 0:
            return

        board = None
        try:
            board = ln.read_board_from_file(f)
        finally:
            if board is None:
                print("Could not load board from file '{}'".format(f))
            else:
                self._load_board(board)

    def _load_board(self, board):
        self.game_state.board = board
        for x in range(board.width):
            for y in range(board.height):
                self.board_buttons[x][y].set_by_tile(board.get_tile_at(x, y))

    def start_game(self, _e):
        if self.game_state.board is None or self.game_state.started:
            return

        self.game_state.start()
        self.toss()
        self.update_statusbar()

    def clear_game(self):
        pass  # todo

    def toss(self):
        if not self.game_state.started or self.game_state.tossed:
            return

        for i in range(random.randint(11, 17)):
            self.game_state.rolled_numbers[0] = random.randint(1, 6)
            self.game_state.rolled_numbers[1] = random.randint(1, 6)
            self.game_state.rolled_colors[0] = random.choice(Color.ref_list(True))
            self.game_state.rolled_colors[1] = random.choice(Color.ref_list(True))

            self.color_dice_1.set_color(self.game_state.rolled_colors[0])
            self.color_dice_2.set_color(self.game_state.rolled_colors[1])
            self.number_dice_1['text'] = str(self.game_state.rolled_numbers[0]).replace('6', '?')
            self.number_dice_2['text'] = str(self.game_state.rolled_numbers[1]).replace('6', '?')
            self.update()

            time.sleep(0.075 + 0.125 * (i/17))

        self.game_state.inc_toss_count()

    def commit(self, _e):
        if not self.game_state.started or not self.game_state.tossed:
            return

        jokers_used = 0

        if len(self.game_state.crossed_tiles_to_commit) == 0:
            if not msgbox.askyesno(title="Pass?", message="Would you like to pass this turn?"):
                return
        else:
            if len(self.game_state.crossed_tiles_to_commit) not in self.game_state.rolled_numbers:
                if 6 in self.game_state.rolled_numbers:
                    jokers_used += 1
                else:
                    return  # invalid set of crosses

            if self.game_state.board.get_color_at(self.game_state.crossed_tiles_to_commit[0][0], self.game_state.crossed_tiles_to_commit[0][1]) not in self.game_state.rolled_colors:
                jokers_used += 1

            if not self.game_state.use_joker(jokers_used):
                return

        # all checks passed, update game state
        for (x, y) in self.game_state.crossed_tiles_to_commit:
            self.board_buttons[x][y].commit()
            tile = self.game_state.board.get_tile_at(x, y)
            self.game_state.colors_crossed[tile.color] += 1
            self.game_state.columns_crossed[x] += 1
            if tile.star:
                self.game_state.stars_crossed += 1

        # reset tiles to commit list
        self.game_state.crossed_tiles.extend(self.game_state.crossed_tiles_to_commit)
        self.game_state.crossed_tiles_to_commit = []

        self.progress_var.set(self.game_state.toss_counter)
        self.update_statusbar()

        if self.game_state.toss_counter == 30:
            score = self.calc_score()
            msgbox.showinfo("Game Over", "Game over, final score:\n\n"
                                         "Color bonus:\t{1[0]:>3}\n"
                                         "Column bonus:\t{1[1]:>3}\n"
                                         "Joker bonus:\t{1[2]:>3}\n"
                                         "Star penalty:\t{1[3]:>3}\n"
                                         "-----------------------------\n"
                                         "Total score:\t{0}".format(sum(score), score))
            self.game_state.finish()
            return
        else:
            self.game_state.tossed = False
            self.toss()

    def check_click(self, x, y):
        if not self.game_state.started or not self.game_state.tossed:
            return False  # todo: error messages

        # no already committed cross
        if (x, y) in self.game_state.crossed_tiles:
            return False

        # always be able to remove a cross to commit
        if (x, y) in self.game_state.crossed_tiles_to_commit:
            self.game_state.crossed_tiles_to_commit.remove((x, y))
            self.update_statusbar()
            return True

        # Xs left to place?
        if len(self.game_state.crossed_tiles_to_commit) >= min(max(self.game_state.rolled_numbers), 5):
            return False

        # color was tossed?
        if Color.UNINITIALIZED not in self.game_state.rolled_colors and self.game_state.board.get_color_at(x, y) not in self.game_state.rolled_colors:
            return False

        # only one component
        if len(self.game_state.crossed_tiles_to_commit) > 0:
            component = self.game_state.board.get_component(self.game_state.crossed_tiles_to_commit[0][0], self.game_state.crossed_tiles_to_commit[0][1])
            if (x, y) not in component:
                return False

        # column 7 (H, the middle) reachable?
        if not x == 7:
            coords = set(self.game_state.crossed_tiles).union(set(self.game_state.crossed_tiles_to_commit))
            coords.add((x, y))
            reachable_coords = ln._get_connected_coords(coords, (x, y))[0]

            hcol_reached = False
            for i in range(self.game_state.board.height):
                if (7, i) in reachable_coords:
                    hcol_reached = True

            if not hcol_reached:
                return False

        # all checks passed
        self.game_state.crossed_tiles_to_commit.append((x, y))
        self.update_statusbar()
        return True

    def update_statusbar(self, error_msg=None):
        state = self.game_state

        if error_msg:
            self.statusbar['text'] = error_msg
            return

        if not state.started:
            self.statusbar['text'] = "Game not started yet"
            return

        turn = "Turn {:>2}/30".format(state.toss_counter)
        jokers = "Jokers left: " + str(state.joker_count)
        placed_crosses = "Crosses placed: " + str(len(state.crossed_tiles_to_commit))
        score = "Score: " + str(sum(self.calc_score()))

        self.statusbar['text'] = "{} {} {} {}".format(turn, jokers, placed_crosses, score)
        self.update_column_finished_indicators()

    def calc_score(self):
        state = self.game_state
        return [sum([5 if v == 21 else 0 for v in state.colors_crossed.values()]),  # color bonus
                sum([ln.POINTS_PER_COLUMN[i] if v == 7 else 0 for i, v in
                     zip(range(state.board.width), state.columns_crossed)]),  # column bonus
                state.joker_count,  # joker bonus
                (-2) * (state.board.width - state.stars_crossed)]  # star penalty

    def update_column_finished_indicators(self):
        for i in range(len(self.board_column_point_labels)):
            if self.game_state.columns_crossed[i] == self.game_state.board.height:
                self.board_column_point_labels[i]['bg'] = 'green'


def main():
    random.seed()

    root = tk.Tk()
    root.wm_title("Noch mal! Single Player Challenge")
    root.attributes('-type', 'dialog')
    app = Application(master=root)

    app.mainloop()


if __name__ == '__main__':
    main()
