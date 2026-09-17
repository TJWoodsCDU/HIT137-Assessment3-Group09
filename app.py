import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog as tkfiledialog
import cv2
import random


def main():
    # Init window
    window = tk.Tk()
    window.title("Puzzle Game")
    window.geometry("640x480")


    # Define widgets

    # set game size
    rdio_lbl = tk.Label(
        window,
        text = "Select Game Size:"
    )

    g_size = tk.IntVar()
    values = {
        "3x3": 3,
        "4x4": 4,
        "5x5": 5
    }
    rdios = []
    for (text, value) in values.items():
        rdios.append(
            ttk.Radiobutton(
                window,
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
    file_select_btn = tk.Button(window, text="Select Image", command=upload_file)

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
        # TODO:
        print("PLAY GAME")

    enter_btn = tk.Button(
        window,
        text = "Save & Enter",
        command = lambda: play_game() if validate_start_game() else None
    )

    # Place widgets

    # TODO: make it look pretty
    rdio_lbl.pack()
    for rdio in rdios:
        rdio.pack()
    file_select_btn.pack()
    enter_btn.pack()


    # Run mainloop
    window.mainloop()



if __name__ == "__main__":
    main()
