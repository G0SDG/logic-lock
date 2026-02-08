import tkinter as tk

class GUI: 
    def __init__(self, master):
        self.master = master
        master.title("Testing GUI")

        self.label = tk.Label(master, text="This is a test GUI")
        self.label.pack()

        self.greet_button = tk.Button(master, text="Greet", command=self.greet)
        self.greet_button.pack()

        self.close_button = tk.Button(master, text="Close", command=master.quit)
        self.close_button.pack()

    def greet(self):
        print("Hello, World!")

root = tk.Tk()
gui = GUI(root)
root.mainloop()