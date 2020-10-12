#!/usr/bin/env python3

import sys
import os
from enum import Enum, auto

import tkinter as tk
from threading import Thread, Event

from PIL import Image, ImageTk
import tkinter.filedialog as tkfd

import libnochmal as ln
from libnochmal import Color


class Tool(Enum):
    PEN = auto()
    FILL = auto()
    STAR = auto()


class ColorButton(tk.Button):
    def __init__(self, master, color, x, y):
        super(ColorButton, self).__init__(master, bg=color.to_rgb(), activebackground=color.to_rgb_secondary(),
                                          font='TkFixedFont', relief="flat", overrelief="flat")
        self.application = master
        self.already_changed = False
        self.color = color
        self.star = False
        self['image'] = self.application.circle_image
        self.x = x
        self.y = y

    def toggle_star(self, value=None):
        if value is not None:
            self.star = value
        else:
            self.star = not self.star
        if self.star:
            self['image'] = self.application.star_image
        else:
            self['image'] = self.application.circle_image
        self.application.board.set_star_at(self.x, self.y, self.star)

    def change_color(self, color):
        self.color = color
        self.config(bg=color.to_rgb(), activebackground=color.to_rgb_secondary())
        self.application.board.set_color_at(self.x, self.y, self.application.selected_color.get())

    def change_by_tool(self):
        selected_tool = self.application.selected_tool.get()
        if selected_tool == Tool.STAR:
            self.toggle_star()
        elif selected_tool == Tool.PEN:
            self.change_color(self.application.selected_color.get())
        else:  # fill
            pass
            # comp = self.application.board.get_component(self.x, self.y)
            # print(comp)

    def set_by_tile(self, tile):
        self.change_color(tile.color)
        self.toggle_star(tile.star)

    def mouse_entered(self):
        if not self.already_changed:
            self.already_changed = True
            self.change_by_tool()

    def mouse_up(self):
        self.already_changed = False


class ColorRadiobutton(tk.Radiobutton):
    def __init__(self, master, color, variable):
        super(ColorRadiobutton, self).__init__(master, variable=variable, value=color, bg=color.to_rgb(),
                                               activebackground=color.to_rgb_secondary())


class EnumVar(tk.Variable):
    """Value holder for strings variables."""
    _default = ""

    def __init__(self, enum, default=None, master=None, value=None, name=None):
        """Construct a color variable."""
        tk.Variable.__init__(self, master, value, name)
        self.enum = enum
        self._default = default

    def get(self):
        """Return value of variable as color."""
        value = self._tk.globalgetvar(self._name)
        if isinstance(value, self.enum):
            return value

        for c in self.enum:
            if str(c) == value:
                return c

        return self._default


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.old_color = Color.UNINITIALIZED
        self.grid()
        self.filename = tk.StringVar(self)

        # use board filename if one was given on the command line
        if len(sys.argv) > 1:
            self.filename.set(sys.argv[1])
        else:
            self.filename.set('/tmp/board.dat')

        # load star and circle image
        script_path = os.path.dirname(os.path.realpath(__file__))
        self.star_image = ImageTk.PhotoImage(Image.open(script_path + '/img/star.png'))
        self.circle_image = ImageTk.PhotoImage(Image.open(script_path + '/img/circle.png'))

        # tool tool bar
        self.top_tool_tool_bar = tk.Frame(self)
        self.top_tool_tool_bar.grid(row=0, column=0, columnspan=6, sticky='W')

        self.selected_tool = EnumVar(Tool, default=Tool.PEN, master=master, value=Tool.PEN)
        self.radio_pen = tk.Radiobutton(self.top_tool_tool_bar, text='Pen', variable=self.selected_tool, value=Tool.PEN)
        self.radio_fill = tk.Radiobutton(self.top_tool_tool_bar, text='Fill', variable=self.selected_tool, value=Tool.FILL)
        self.radio_star = tk.Radiobutton(self.top_tool_tool_bar, text='Star', variable=self.selected_tool, value=Tool.STAR)
        self.radio_pen.pack(side='left')
        self.radio_fill.pack(side='left')
        self.radio_star.pack(side='left')

        # color tool bar
        self.selected_color = EnumVar(Color, default=Color.UNINITIALIZED, master=master, value=Color.RED)
        self.radio_r = ColorRadiobutton(self, Color.RED, self.selected_color)
        self.radio_o = ColorRadiobutton(self, Color.ORANGE, self.selected_color)
        self.radio_y = ColorRadiobutton(self, Color.YELLOW, self.selected_color)
        self.radio_g = ColorRadiobutton(self, Color.GREEN, self.selected_color)
        self.radio_b = ColorRadiobutton(self, Color.BLUE, self.selected_color)
        self.radio_w = ColorRadiobutton(self, Color.WHITE, self.selected_color)

        self.radio_r.grid(row=0, column=9)
        self.radio_o.grid(row=0, column=10)
        self.radio_y.grid(row=0, column=11)
        self.radio_g.grid(row=0, column=12)
        self.radio_b.grid(row=0, column=13)
        self.radio_w.grid(row=0, column=14)

        # board buttons
        self.board_buttons = []
        for x in range(15):
            self.board_buttons.append([])
            for y in range(7):
                btn = ColorButton(self, Color.UNINITIALIZED, x, y)
                btn.bind("<Button-1>", self.mouse_down)
                btn.bind("<ButtonRelease-1>", self.mouse_up)
                btn.bind("<B1-Motion>", self.mouse_motion)
                btn.bind("<Button-3>", self.mouse_sec_down)
                btn.bind("<ButtonRelease-3>", self.mouse_sec_up)
                btn.bind("<B3-Motion>", self.mouse_motion)

                btn.grid(row=(1 + y), column=x)
                self.board_buttons[x].append(btn)

        # generate tool bar
        self.generate_bar = tk.Frame(self)
        self.generate_bar.grid(row=8, column=0, columnspan=15, sticky='W')
        self.btn_gen = tk.Button(self.generate_bar, text='Generate Board', command=self.generate_a_board)
        self.btn_cancel = tk.Button(self.generate_bar, text='Cancel Generation', command=self.cancel_generation)
        self.btn_gen.pack(side='left')
        self.btn_cancel.pack(side='left')

        self.timer = None
        self.gen_thread = None
        self.stopFlag = None
        self.gen_board = None
        self.gen_state = None

        # bottom buttons
        self.bottom_bar = tk.Frame(self)
        self.bottom_bar.grid(row=9, column=0, columnspan=15, sticky='W')

        self.btn_load = tk.Button(self.bottom_bar, text='Load', command=self.load_board)
        self.btn_load.pack(side='left')

        self.btn_save_as = tk.Button(self.bottom_bar, text='Save As', command=self.choose_file_to_save)
        self.btn_save_as.pack(side='left')

        self.lbl_file = tk.Label(self.bottom_bar, textvariable=self.filename)
        self.lbl_file.pack(side='left')

        self.btn_save = tk.Button(self, text='Save', command=self.save_board)
        self.btn_save.grid(row=9, column=13, columnspan=2, sticky='E')

        # try to import the board from the filename
        try:
            self.board = ln.read_board_from_file(self.filename.get())
            self.import_board(self.board)
        except FileNotFoundError:
            print("File {} does not exist, creating new board.".format(self.filename.get()))
            self.board = ln.Board()  # create new board

    def mouse_down(self, e):
        self.update_containing_button(e)

    def mouse_up(self, e):
        for col in self.board_buttons:
            for button in col:
                button.mouse_up()

    def mouse_motion(self, e):
        if self.selected_tool.get() == Tool.PEN:
            self.update_containing_button(e)

    def update_containing_button(self, e):
        for col in self.board_buttons:
            for button in col:
                if self.winfo_containing(e.x_root, e.y_root) is button:
                    button.mouse_entered()

    def mouse_sec_down(self, e):
        self.old_color = self.selected_color.get()
        self.selected_color.set(Color.WHITE)
        self.mouse_down(e)

    def mouse_sec_up(self, e):
        self.mouse_up(e)
        self.selected_color.set(self.old_color)

    def import_board(self, board):
        for x in range(board.width):
            for y in range(board.height):
                self.board_buttons[x][y].set_by_tile(board.get_tile_at(x, y))

    def load_board(self):
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
                self.import_board(board)

    def choose_file_to_save(self):
        f = tkfd.asksaveasfilename(defaultextension='.dat')
        if len(f) == 0:
            return

        self.filename.set(f)

    def save_board(self):
        for x in range(self.board.width):
            for y in range(self.board.height):
                color = self.board_buttons[x][y].color
                star = self.board_buttons[x][y].star
                self.board.set_tile_at(x, y, ln.Tile(color, star))

        ln.write_board_to_file(self.board, self.filename.get())

    def generate_a_board(self):
        self.gen_board = ln.Board()
        self.gen_state = ln.BacktrackingState()
        self.stopFlag = Event()
        self.timer = ln.PerpetualTimer(self.stopFlag, lambda: self.import_board(self.gen_board), 1.0)
        self.timer.start()

        self.gen_thread = Thread(target=ln.fill_smart, args=(self.gen_board, self.gen_state))
        self.gen_thread.start()

    def cancel_generation(self):
        # this will stop the timer
        # todo: stop the gen thread gracefully
        self.stopFlag.set()


root = tk.Tk()
root.wm_title("Noch mal! Board Designer")
root.attributes('-type', 'dialog')
app = Application(master=root)

app.mainloop()
