#!/usr/bin/env python

import sys
import tkinter as tk
import tkinter.filedialog as tkfd
import libnochmal as ln


RED = "#FA0046"
ORANGE = "#FA8200"
YELLOW = "#FADC00"
GREEN = "#96BE1E"
BLUE = "#5AC8FA"


def color_to_rgb(color):
    if color == 'r': return RED
    if color == 'o': return ORANGE
    if color == 'y': return YELLOW
    if color == 'g': return GREEN
    if color == 'b': return BLUE
    return "white"


def rgb_to_color(rgb):
    if rgb == RED:    return 'r'
    if rgb == ORANGE: return 'o'
    if rgb == YELLOW: return 'y'
    if rgb == GREEN:  return 'g'
    if rgb == BLUE:   return 'b'
    return "w"


def secondary_color(color):
    if color == RED or color == 'r': return '#FB5986'
    if color == ORANGE or color == 'o': return '#FBAD59'
    if color == YELLOW or color == 'y': return '#FBE859'
    if color == GREEN or color == 'g': return '#BAD46C'
    if color == BLUE or color == 'b': return '#93DBFB'
    return '#ececec'


class ColorButton(tk.Button):
    def __init__(self, master, text='w', bg="white", activebackground=secondary_color('w')):
        super(ColorButton, self).__init__(master, text=text, bg=bg, activebackground=activebackground,
                                          font='TkFixedFont', relief="flat", overrelief="flat")
        self.application = master
        self.already_changed = False
        self.star = False

    def toggle_star(self):
        self.star = not self.star
        if self.star:
            self['text'] = self['text'].upper()
        else:
            self['text'] = self['text'].lower()

    def change(self):
        if self.application.selected_tool.get() == 'star':
            self.toggle_star()
        else:
            color = self.application.selected_color.get()
            self.config(text=color, bg=color_to_rgb(color), activebackground=secondary_color(color))
            if self.star:
                self['text'] = color.upper()

    def set_by_tile(self, tile):
        self.config(text=tile.color, bg=color_to_rgb(tile.color), activebackground=secondary_color(tile.color))
        if tile.star:
            self.star = True
            self['text'] = tile.color.upper()

    def mouse_entered(self):
        if not self.already_changed:
            self.already_changed = True
            self.change()

    def mouse_up(self):
        self.already_changed = False


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.old_color = 'w'
        self.grid()
        self.filename = tk.StringVar(self)

        # use board filename if one was given on the command line
        if len(sys.argv) > 1:
            self.filename.set(sys.argv[1])
        else:
            self.filename.set('/tmp/board.dat')

        # tool tool bar
        self.selected_tool = tk.StringVar(master, value='pen')
        self.radio_pen = tk.Radiobutton(self, text='Pen', variable=self.selected_tool, value='pen')
        self.radio_fill = tk.Radiobutton(self, text='Fill', variable=self.selected_tool, value='fill')
        self.radio_star = tk.Radiobutton(self, text='Star', variable=self.selected_tool, value='star')
        self.radio_pen.grid(row=0, column=0, columnspan=2, sticky='W')
        self.radio_fill.grid(row=0, column=2, columnspan=2, sticky='W')
        self.radio_star.grid(row=0, column=4, columnspan=2, sticky='W')

        # color tool bar
        self.selected_color = tk.StringVar(master, value='r')
        self.radio_r = tk.Radiobutton(self, variable=self.selected_color, value='r', bg=RED, activebackground=secondary_color(RED))
        self.radio_o = tk.Radiobutton(self, variable=self.selected_color, value='o', bg=ORANGE, activebackground=secondary_color(ORANGE))
        self.radio_y = tk.Radiobutton(self, variable=self.selected_color, value='y', bg=YELLOW, activebackground=secondary_color(YELLOW))
        self.radio_g = tk.Radiobutton(self, variable=self.selected_color, value='g', bg=GREEN, activebackground=secondary_color(GREEN))
        self.radio_b = tk.Radiobutton(self, variable=self.selected_color, value='b', bg=BLUE, activebackground=secondary_color(BLUE))
        self.radio_w = tk.Radiobutton(self, variable=self.selected_color, value='w', bg="white")
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
                btn = ColorButton(self)
                btn.bind("<Button-1>", self.mouse_down)
                btn.bind("<ButtonRelease-1>", self.mouse_up)
                btn.bind("<B1-Motion>", self.mouse_motion)
                btn.bind("<Button-3>", self.mouse_sec_down)
                btn.bind("<ButtonRelease-3>", self.mouse_sec_up)
                btn.bind("<B3-Motion>", self.mouse_motion)

                btn.grid(row=(1+y), column=x)
                self.board_buttons[x].append(btn)

        # bottom buttons
        self.bottom_bar = tk.Frame(self)
        self.bottom_bar.grid(row=8, column=0, columnspan=15, sticky='W')

        self.btn_load = tk.Button(self.bottom_bar, text='Load', command=self.load_board)
        self.btn_load.pack(side='left')

        self.btn_save_as = tk.Button(self.bottom_bar, text='Save As', command=self.choose_file_to_save)
        self.btn_save_as.pack(side='left')

        self.lbl_file = tk.Label(self.bottom_bar, textvariable=self.filename)
        self.lbl_file.pack(side='left')

        self.btn_save = tk.Button(self, text='Save', command=self.save_board)
        self.btn_save.grid(row=8, column=13, columnspan=2, sticky='E')

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
        if self.selected_tool.get() == 'pen':
            self.update_containing_button(e)

    def update_containing_button(self, e):
        for col in self.board_buttons:
            for button in col:
                if self.winfo_containing(e.x_root, e.y_root) is button:
                    button.mouse_entered()

    def mouse_sec_down(self, e):
        self.old_color = self.selected_color.get()
        self.selected_color.set('w')
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
                color = self.board_buttons[x][y]['text'].lower()
                star = self.board_buttons[x][y].star
                self.board.set_tile_at(x, y, ln.Tile(color, star))

        ln.write_board_to_file(self.board, self.filename.get())


root = tk.Tk()
root.wm_title("Noch mal! Board Designer")
root.attributes('-type', 'dialog')
app = Application(master=root)

app.mainloop()
