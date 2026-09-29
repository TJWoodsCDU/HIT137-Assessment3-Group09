import random
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import cv2 as cv
from PIL import Image, ImageTk

from puzzle import ImageProcessor, PuzzleBoard
from scrambling import horizontal


class BasePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self._controller = controller

    @property
    def controller(self):
        return self._controller

    def on_show(self) -> None:
        pass


class GamePage(BasePage):
    HINT_LIMIT = 3
    DISPLAY_SIZE = 400

    GRID_COLOUR = "#cfcfcf"
    SELECT_COLOUR = "#ff8c1a"
    TICK_COLOUR = "#21c25a"
    TICK_SHADOW = "#0c4023"
    HINT_COLOUR = "#1e90ff"

    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        self.__processor = ImageProcessor(self.DISPLAY_SIZE)
        self.__board = None
        self.__original_image = None
        self.__selected = None
        self.__hint = None
        self.__hints_used = 0
        self.__locked = False
        self.__puzzle_photo = None
        self.__original_photo = None

        controls = tk.Frame(self)

        tk.Label(controls, text="Grid size:").pack(side="left", padx=(0, 4))

        self.__grid_choice = tk.StringVar(value="3 x 3")
        self.__grid_box = ttk.Combobox(
            controls,
            textvariable=self.__grid_choice,
            values=("3 x 3", "4 x 4", "5 x 5"),
            state="readonly",
            width=6,
        )
        self.__grid_box.pack(side="left", padx=(0, 10))
        self.__grid_box.bind("<<ComboboxSelected>>", self.__on_grid_changed)

        self.__load_btn = ttk.Button(
            controls, text="Load Image", command=self.__on_load_image
        )
        self.__load_btn.pack(side="left", padx=4)

        ttk.Separator(controls, orient="vertical").pack(
            side="left", fill="y", padx=10
        )

        self.__hint_btn = ttk.Button(controls, text="Hint", command=self.__on_hint)
        self.__hint_btn.pack(side="left", padx=4)

        self.__solve_btn = ttk.Button(controls, text="Solve", command=self.__on_solve)
        self.__solve_btn.pack(side="left", padx=4)

        self.__back_btn = ttk.Button(
            controls, text="< Start Page", command=self.__on_back
        )
        self.__back_btn.pack(side="left", padx=4)

        self.__original_label = tk.Label(self, text="Original (reference only)")
        self.__puzzle_label = tk.Label(self, text="Puzzle (click the tiles)")

        self.__original_canvas = tk.Canvas(
            self,
            width=self.DISPLAY_SIZE,
            height=self.DISPLAY_SIZE,
            highlightthickness=1,
            highlightbackground="#999999",
            background="#1c1c1c",
        )
        self.__puzzle_canvas = tk.Canvas(
            self,
            width=self.DISPLAY_SIZE,
            height=self.DISPLAY_SIZE,
            highlightthickness=1,
            highlightbackground="#999999",
            background="#1c1c1c",
        )

        self.__puzzle_canvas.bind("<Button-1>", self.__on_left_click)
        self.__puzzle_canvas.bind("<Shift-Button-1>", self.__on_shift_left_click)
        self.__puzzle_canvas.bind("<Button-3>", self.__on_right_click)
        self.__puzzle_canvas.bind("<Button-2>", self.__on_right_click)

        self.__status = tk.Label(
            self, text="No image loaded.", anchor="w",
            font=("TkDefaultFont", 10, "bold"),
        )
        self.__message = tk.Label(self, text="", anchor="w", fg="#1a7f37")

        controls.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 6))
        self.__original_label.grid(row=1, column=0, pady=(0, 2))
        self.__puzzle_label.grid(row=1, column=1, pady=(0, 2))
        self.__original_canvas.grid(row=2, column=0, padx=10)
        self.__puzzle_canvas.grid(row=2, column=1, padx=10)
        self.__status.grid(row=3, column=0, columnspan=2, sticky="w", padx=12, pady=(8, 0))
        self.__message.grid(row=4, column=0, columnspan=2, sticky="w", padx=12, pady=(0, 10))

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def on_show(self) -> None:
        state = self._controller.game_state

        try:
            grid_size = state.get_size()
            path = state.get_img_path()
        except (TypeError, ValueError):
            messagebox.showerror(
                "Cannot start game",
                "The grid size or image file was not set correctly.",
            )
            return

        self.__grid_choice.set(f"{grid_size} x {grid_size}")
        self.__start_round(path, grid_size)

    def __start_round(self, path: str, grid_size: int) -> bool:
        try:
            raw_image = ImageProcessor.load(path)
        except ValueError as error:
            messagebox.showerror("Could not open image", str(error))
            return False
        except Exception as error:
            messagebox.showerror(
                "Could not open image",
                f"Something went wrong reading that file.\n\n{error}",
            )
            return False

        prepared = self.__processor.prepare(raw_image, grid_size)

        self.__original_image = prepared
        self.__board = PuzzleBoard(prepared, grid_size)
        self.__board.scramble(random.Random())

        self.__selected = None
        self.__hint = None
        self.__hints_used = 0
        self.__locked = False
        self.__hint_btn.state(["!disabled"])
        self.__solve_btn.state(["!disabled"])
        self.__message.config(text="", fg="#1a7f37")

        size = self.__board.image_size
        for canvas in (self.__original_canvas, self.__puzzle_canvas):
            canvas.config(width=size, height=size)

        self.__draw_original()
        self.__redraw()
        return True

    @staticmethod
    def __to_photo(bgr_image):
        rgb_image = cv.cvtColor(bgr_image, cv.COLOR_BGR2RGB)
        return ImageTk.PhotoImage(Image.fromarray(rgb_image))

    def __draw_original(self) -> None:
        self.__original_photo = self.__to_photo(self.__original_image)
        canvas = self.__original_canvas
        canvas.delete("all")
        canvas.create_image(0, 0, anchor="nw", image=self.__original_photo)

    def __redraw(self) -> None:
        if self.__board is None:
            return

        board = self.__board

        self.__puzzle_photo = self.__to_photo(board.render())
        canvas = self.__puzzle_canvas
        canvas.delete("all")
        canvas.create_image(0, 0, anchor="nw", image=self.__puzzle_photo)

        self.__draw_grid_lines(canvas)
        self.__draw_ticks(canvas)
        self.__draw_selection(canvas)
        self.__draw_hint()
        self.__update_status()

    def __draw_grid_lines(self, canvas) -> None:
        board = self.__board
        size = board.image_size
        step = board.tile_size
        for index in range(1, board.grid_size):
            offset = index * step
            canvas.create_line(offset, 0, offset, size, fill=self.GRID_COLOUR)
            canvas.create_line(0, offset, size, offset, fill=self.GRID_COLOUR)

    def __draw_ticks(self, canvas) -> None:
        board = self.__board
        for position in range(board.tile_count):
            if not board.is_tile_correct(position):
                continue
            left, top, _, _ = board.bounds_of(position)
            x = left + 7
            y = top + 7
            points = (x, y + 8, x + 5, y + 13, x + 14, y + 1)
            canvas.create_line(
                *points, fill=self.TICK_SHADOW, width=5,
                capstyle="round", joinstyle="round",
            )
            canvas.create_line(
                *points, fill=self.TICK_COLOUR, width=3,
                capstyle="round", joinstyle="round",
            )

    def __draw_selection(self, canvas) -> None:
        if self.__selected is None:
            return
        left, top, right, bottom = self.__board.bounds_of(self.__selected)
        canvas.create_rectangle(
            left + 2, top + 2, right - 2, bottom - 2,
            outline=self.SELECT_COLOUR, width=3,
        )

    def __draw_hint(self) -> None:
        self.__original_canvas.delete("hint")
        if self.__hint is None or self.__board is None:
            return

        current_position, home_position = self.__hint
        self.__draw_circle(self.__puzzle_canvas, current_position)
        self.__draw_circle(self.__original_canvas, home_position, tag="hint")

    def __draw_circle(self, canvas, position: int, tag: str = "") -> None:
        left, top, right, bottom = self.__board.bounds_of(position)
        inset = self.__board.tile_size * 0.22
        canvas.create_oval(
            left + inset, top + inset, right - inset, bottom - inset,
            outline=self.HINT_COLOUR, width=3, tags=tag,
        )

    def __update_status(self) -> None:
        board = self.__board
        hints_left = self.HINT_LIMIT - self.__hints_used
        self.__status.config(
            text=(
                f"Moves: {board.moves}     "
                f"Tiles incorrect: {board.tiles_remaining()} of {board.tile_count}     "
                f"Hints left: {hints_left}"
            )
        )

    def __position_from_event(self, event):
        if self.__board is None or self.__locked:
            return None
        x = self.__puzzle_canvas.canvasx(event.x)
        y = self.__puzzle_canvas.canvasy(event.y)
        return self.__board.position_at_pixel(x, y)

    def __on_left_click(self, event) -> None:
        position = self.__position_from_event(event)
        if position is None:
            return

        if self.__selected is None:
            self.__selected = position
            self.__redraw()
        elif self.__selected == position:
            self.__selected = None
            self.__redraw()
        else:
            self.__board.player_swap(self.__selected, position)
            self.__selected = None
            self.__after_move()

    def __on_right_click(self, event) -> None:
        position = self.__position_from_event(event)
        if position is None:
            return
        self.__board.player_rotate(position, 90)
        self.__after_move()

    def __on_shift_left_click(self, event) -> None:
        position = self.__position_from_event(event)
        if position is None:
            return
        self.__board.player_flip(position, horizontal)
        self.__after_move()

    def __after_move(self) -> None:
        self.__hint = None
        self.__redraw()
        self.__check_for_win()

    def __selected_grid_size(self) -> int:
        try:
            return int(self.__grid_choice.get().split("x")[0].strip())
        except (ValueError, IndexError):
            return 3

    def __on_load_image(self) -> None:
        path = filedialog.askopenfilename(
            title="Select Game Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return

        grid_size = self.__selected_grid_size()
        if self.__start_round(path, grid_size):
            state = self._controller.game_state
            state.set_img_path(path)
            state.set_size(grid_size)

    def __on_grid_changed(self, event=None) -> None:
        grid_size = self.__selected_grid_size()
        state = self._controller.game_state
        try:
            path = state.get_img_path()
        except (TypeError, ValueError):
            return
        if self.__start_round(path, grid_size):
            state.set_size(grid_size)

    def __on_hint(self) -> None:
        if self.__board is None or self.__locked:
            return
        if self.__hints_used >= self.HINT_LIMIT:
            self.__hint_btn.state(["disabled"])
            return

        wrong_positions = self.__board.incorrect_positions()
        if not wrong_positions:
            return

        misplaced = [
            position
            for position in wrong_positions
            if self.__board.home_of(position) != position
        ]
        position = random.choice(misplaced or wrong_positions)

        self.__hint = (position, self.__board.home_of(position))
        self.__hints_used += 1
        if self.__hints_used >= self.HINT_LIMIT:
            self.__hint_btn.state(["disabled"])

        self.__redraw()

    def __on_solve(self) -> None:
        if self.__board is None:
            return

        self.__board.solve()
        self.__selected = None
        self.__hint = None
        self.__locked = True
        self.__hint_btn.state(["disabled"])
        self.__solve_btn.state(["disabled"])
        self.__redraw()
        self.__message.config(
            text="Puzzle solved automatically. Load another image to play again.",
            fg="#0b6bcb",
        )

    def __on_back(self) -> None:
        self._controller.show_start_page()

    def __check_for_win(self) -> None:
        if self.__board is None or not self.__board.is_solved():
            return

        self.__locked = True
        self.__selected = None
        self.__hint = None
        self.__hint_btn.state(["disabled"])
        self.__solve_btn.state(["disabled"])
        self.__redraw()
        self.__message.config(
            text=(
                f"Complete! Restored in {self.__board.moves} moves. "
                "Load another image to keep playing."
            ),
            fg="#1a7f37",
        )
        messagebox.showinfo(
            "Puzzle complete",
            f"Well done - the picture is fully restored!\n\n"
            f"Moves used: {self.__board.moves}\n"
            f"Hints used: {self.__hints_used}\n\n"
            "Load another image to play again.",
        )