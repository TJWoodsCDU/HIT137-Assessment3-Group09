import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog as tkfiledialog
import cv2
import random

class GameConfig:
    def __init__(self, size, img_path, ):
        self.__size = size
        self.__img_path = img_path

    def get_size(self):
        return self.__size

    def get_img_path(self):
        return self.__img_path


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
        frame.tkraise()


class StartPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        # Define widgets

        # set game size
        rdio_lbl = tk.Label(
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
            nonlocal file_path
            file_path = tkfiledialog.askopenfilename(title="Select Game Image", filetypes=[("Image File", ('*.png', '*.jpg', '*.bmp'))])
            print(f"Debug: Selected file = {file_path} of type {type(file_path)}")

        file_path = ""
        file_select_btn = ttk.Button(self, text="Select Image", command=upload_file)

        # enter game
        def validate_start_game():
            valid = True
            if not (3 <= g_size.get() <= 5):
                valid = False
                tk.messagebox.showwarning(title="Must select a game size.", message="Select a game size from the radio buttons.")

            if not (file_path):
                valid = False
                tk.messagebox.showwarning(title="Must select an image file.", message="Select a file from the file selector.")

            return valid

        def play_game():
            "Assumes valid start variables"
            # TODO:
            print(f"Debug: Enter Game of size {g_size.get()} with image {file_path}")
            controller.show_frame(GamePage)

        enter_btn = ttk.Button(
            self,
            text = "Save & Enter",
            command = lambda: play_game() if validate_start_game() else None
        )

        # Place widgets
        # TODO: make it look pretty
        rdio_lbl.grid(row=0, column=0)
        i = 0
        for rdio in rdios:
            rdio.grid(row=1+i, column=0)
            i += 1
        file_select_btn.grid(row=1, column=1)
        enter_btn.grid(row=1+i-1, column=1)


class GamePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        l = tk.Label(self, text="Test", fg="red")
        l.grid(row=1, column=1)


def main():
    # Init window
    window = App()
    window.title("Puzzle Game")
    window.geometry("640x480")


    # Run mainloop
    window.mainloop()



if __name__ == "__main__":
    main()
