import tkinter as tk
from game.game import Flappybird

if __name__ == "__main__":
    root = tk.Tk() 
    root.title("Drawing Applicaiton")
    app = Flappybird(root)
    app.start()
    root.mainloop()


