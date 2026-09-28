from puzzle import ImageProcessor, PuzzleBoard
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog as tkfiledialog
import cv2 as cv
import pathlib
from PIL import Image, ImageTk
import random

class GameState:
    def __init__(self, size=None, img_path=None):
        self.__size = size
        self.__img_path = img_path

    def set_size(self, size):
        self.__size = size

    def set_img_path(self, img_path):
        self.__img_path = img_path

    def get_size(self) -> int:
        return int(self.__size)

    def get_img_path(self) -> str:
        return str(self.__img_path)


class App(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)

        container.grid_rowconfigure(0, weight = 1)
        container.grid_columnconfigure(0, weight = 1)

        self.frames = {}

        for F in (StartPage, GamePage):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(StartPage)

    def show_frame(self, controller):
        frame = self.frames[controller]

        # update page prior to showing
        if hasattr(frame, "on_show"):
            frame.on_show()
        # show page
        frame.tkraise()


class StartPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        # Define widgets

        # set game size
        self.rdio_lbl = tk.Label(
            self,
            text = "Select Game Size:"
        )

        g_size = tk.IntVar(self, 3)
        values = {
            "3x3": 3,
            "4x4": 4,
            "5x5": 5
        }
        rdios = []
        for (text, value) in values.items():
            rdios.append(
                ttk.Radiobutton(
                    self,
                    text = text,
                    variable = g_size,
                    value = value
                )
            )

        # select image file
        def upload_file():
            """
            Opens file picker dialog.
            """
            nonlocal file_path
            file_path = tkfiledialog.askopenfilename(title="Select Game Image", filetypes=[("Image File", ('*.png', '*.jpg', '*.bmp'))])
            print(f"Debug: Selected file = {file_path} of type {type(file_path)}")

        file_path = ""
        self.file_select_btn = ttk.Button(self, text="Select Image", command=upload_file)

        # play game
        def validate_start_game() -> bool:
            """
            Determine whether game variables are valid.
            Returns True if yes, else False.
            """
            valid = True
            if not (3 <= g_size.get() <= 5):
                valid = False
                tk.messagebox.showwarning(title="Must select a game size.", message="Select a game size from the radio buttons.")

            if not (file_path):
                valid = False
                tk.messagebox.showwarning(title="Must select an image file.", message="Select a file from the file selector.")

            return valid

        def play_game():
            """
            Start game.
            Updates game state class.
            Switches pages.
            Assumes valid start variables.
            """
            print(f"Debug: Enter Game of size {g_size.get()} with image {file_path}")
            game_state.set_img_path(file_path)
            game_state.set_size(g_size.get())
            controller.show_frame(GamePage)

        self.enter_btn = ttk.Button(
            self,
            text = "Save & Enter",
            command = lambda: play_game() if validate_start_game() else None
        )

        # Place widgets
        # TODO: make it look pretty
        self.rdio_lbl.grid(row=0, column=0)
        i = 0
        for rdio in rdios:
            rdio.grid(row=1+i, column=0)
            i += 1
        self.file_select_btn.grid(row=1, column=1)
        self.enter_btn.grid(row=1+i-1, column=1)


class GamePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        # Puzzle processing
        self.processor = ImageProcessor()
        self.board = None

        # Define widgets

        # Original image
        self.original_lbl = tk.Label(self, text="Original")
        # initialise image to None so it will load on app launch
        img = None
        self.original_img = tk.Label(self, text="No image loaded")

        # Puzzle image
        self.puzzle_lbl = tk.Label(self, text="Puzzle")
        self.puzzle_img = tk.Label(self, text="No puzzle loaded") 

        self.puzzle_img.bind("<Button-1>", self.on_puzzle_click)

        self.selected_tile = None

        self.hints_used = 0
        self.max_hints = 3

        # Game information
        self.status_label = ttk.Label(
            self,
            text="Moves: 0 | Tiles remaining: 0"
        )

        # Puzzle controls
        self.controls = ttk.Frame(self)

        self.rotate_left_btn = ttk.Button(
            self.controls,
            text="Rotate Left",
            command=lambda: self.rotate_selected(-90)
        )

        self.rotate_right_btn = ttk.Button(
            self.controls,
            text="Rotate Right",
            command=lambda: self.rotate_selected(90)
        )

        self.flip_btn = ttk.Button(
            self.controls,
            text="Flip",
            command=self.flip_selected
        )

        self.hint_btn = ttk.Button(
            self.controls,
            text="Hint",
            command=self.show_hint
        )

        self.solve_btn = ttk.Button(
            self.controls,
            text="Solve",
            command=self.solve_puzzle
        )

        # Place widgets
        # TODO: make it look pretty
        self.original_lbl.grid(row=0, column=0)
        self.original_img.grid(row=1, column=0)
        
        self.puzzle_lbl.grid(row=0, column=1)
        self.puzzle_img.grid(row=1, column=1)

        self.status_label.grid(row=2, column=0, columnspan=2, pady=10)

        self.status_label.grid(
            row=2,
            column=0,
            columnspan=2,
            pady=10
        )

        # Place control buttons
        self.rotate_left_btn.grid(row=0, column=0, padx=5)
        self.rotate_right_btn.grid(row=0, column=1, padx=5)
        self.flip_btn.grid(row=0, column=2, padx=5)
        self.hint_btn.grid(row=0, column=3, padx=5)
        self.solve_btn.grid(row=0, column=4, padx=5)

        # Place controls under puzzle
        self.controls.grid(
            row=3,
            column=0,
            columnspan=2,
            pady=10
        )

        # Place game status
        self.status_label.grid(
            row=2,
            column=0,
            columnspan=2,
            pady=10
        )
        
    def on_show(self):
        path = pathlib.Path(game_state.get_img_path()).resolve()
        if path.is_file():
            cv_img = cv.imread(str(path))
            rgb_img = cv.cvtColor(cv_img, cv.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_img)
            self.img = ImageTk.PhotoImage(pil_img)
            self.original_img.config(image=self.img, text="")

            # Prepare image for the puzzle
            grid_size = game_state.get_size()
            prepared_img = self.processor.prepare(cv_img, grid_size)

            # Create puzzle board
            self.board = PuzzleBoard(prepared_img, grid_size)
            self.hints_used = 0
            self.hint_btn.config(state="normal")

            # Scramble the puzzle
            self.board.scramble(random.Random())

            self.status_label.config(
                text=f"Moves: {self.board.moves} | "
                f"Tiles remaining: {self.board.tiles_remaining()}"
            )

            # Render the scrambled puzzle
            puzzle_cv = self.board.render()

            # Convert OpenCV image for Tkinter
            puzzle_rgb = cv.cvtColor(puzzle_cv, cv.COLOR_BGR2RGB)
            puzzle_pil = Image.fromarray(puzzle_rgb)
            self.puzzle_photo = ImageTk.PhotoImage(puzzle_pil)

            # Show puzzle on the right
            self.puzzle_img.config(
                image=self.puzzle_photo,
                text=""
            )

    def on_puzzle_click(self, event):
        if not hasattr(self, "board"):
            return

        position = self.board.position_at_pixel(event.x, event.y)

        if position is None:
            return

        print(f"Clicked tile: {position}")

        if self.selected_tile is None:
            self.selected_tile = position
            print(f"Selected tile: {position}")
        else:
            self.board.player_swap(self.selected_tile, position)
            self.selected_tile = None

            self.refresh_puzzle()

            print(f"Moves: {self.board.moves}")
            print(f"Tiles remaining: {self.board.tiles_remaining()}")

            if self.board.is_solved():
                tk.messagebox.showinfo(
                    "Puzzle Complete",
                    f"Congratulations! You solved the puzzle in {self.board.moves} moves!"
                )

    def rotate_selected(self, degrees):
        if self.selected_tile is None:
            print("Select a tile first")
            return

        self.board.player_rotate(self.selected_tile, degrees)
        self.refresh_puzzle()

        print(f"Rotated tile: {self.selected_tile}")
        print(f"Moves: {self.board.moves}")
        print(f"Tiles remaining: {self.board.tiles_remaining()}")

    def flip_selected(self):
        if self.selected_tile is None:
            print("Select a tile first")
            return

        self.board.player_flip(self.selected_tile)
        self.refresh_puzzle()

        print(f"Flipped tile: {self.selected_tile}")
        print(f"Moves: {self.board.moves}")
        print(f"Tiles remaining: {self.board.tiles_remaining()}")

    def show_hint(self):
        if self.board is None:
            return

        if self.hints_used >= self.max_hints:
            tk.messagebox.showinfo(
                "Hint",
                "You have already used all 3 hints."
            )
            return

        incorrect = self.board.incorrect_positions()

        if not incorrect:
            tk.messagebox.showinfo(
                "Hint",
                "All tiles are already in the correct position!"
            )
            return

        position = incorrect[0]
        correct_position = self.board.home_of(position)

        current_row, current_col = self.board.cell_of(position)
        correct_row, correct_col = self.board.cell_of(correct_position)

        self.hints_used += 1

        tk.messagebox.showinfo(
            "Hint",
            f"Tile at row {current_row + 1}, column {current_col + 1} "
            f"belongs at row {correct_row + 1}, column {correct_col + 1}.\n\n"
            f"Hints used: {self.hints_used}/{self.max_hints}"
        )

        if self.hints_used >= self.max_hints:
            self.hint_btn.config(state="disabled")
    
    def solve_puzzle(self):
        if self.board is None:
            return

        self.board.solve()
        self.selected_tile = None
        self.refresh_puzzle()

        self.status_label.config(
            text=f"Moves: {self.board.moves} | "
                 f"Tiles remaining: {self.board.tiles_remaining()}"
        )

        tk.messagebox.showinfo(
            "Puzzle Solved",
            "The puzzle has been solved!"
        )
    
    def refresh_puzzle(self):
        puzzle_cv = self.board.render()

        puzzle_rgb = cv.cvtColor(
            puzzle_cv,
            cv.COLOR_BGR2RGB
        )

        puzzle_pil = Image.fromarray(puzzle_rgb)

        self.puzzle_photo = ImageTk.PhotoImage(puzzle_pil)

        self.puzzle_img.config(
            image=self.puzzle_photo,
            text=""
        )

        self.status_label.config(
            text=f"Moves: {self.board.moves} | Tiles remaining: {self.board.tiles_remaining()}"
        )

def main():
    # Init window
    global game_state
    game_state = GameState()
    window = App()
    window.title("Puzzle Game")
    window.geometry("640x480")


    # Run mainloop
    window.mainloop()



if __name__ == "__main__":
    main()
