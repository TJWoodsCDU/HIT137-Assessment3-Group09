import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog as tkfiledialog
from tkinter import messagebox

from UI import BasePage, GamePage


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

        self.game_state = GameState()

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

    def show_start_page(self):
        self.show_frame(StartPage)


class StartPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

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
            chosen = tkfiledialog.askopenfilename(title="Select Game Image", filetypes=[("Image File", ('*.png', '*.jpg', '*.jpeg', '*.bmp'))])
            if chosen:
                file_path = chosen

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
                messagebox.showwarning(title="Must select a game size.", message="Select a game size from the radio buttons.")

            if not (file_path):
                valid = False
                messagebox.showwarning(title="Must select an image file.", message="Select a file from the file selector.")

            return valid

        def play_game():
            """
            Start game.
            Updates game state class.
            Switches pages.
            Assumes valid start variables.
            """
            controller.game_state.set_img_path(file_path)
            controller.game_state.set_size(g_size.get())
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


def main():
    # Init window
    window = App()
    window.title("Puzzle Game")
    window.geometry("900x580")
    window.minsize(880, 560)

    # Run mainloop
    window.mainloop()


if __name__ == "__main__":
    main()