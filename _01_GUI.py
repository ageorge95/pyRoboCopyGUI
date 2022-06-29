import sys
sys.path.insert(0, 'CustomTkinter')

from CustomTkinter import customtkinter
from tkinter import *
from tkinterdnd2 import *
from tkinter.scrolledtext import ScrolledText

class App():
    def __init__(self,
                 frame):

        label_current_status = customtkinter.CTkLabel(master=frame,
                                                      text='Current Status')
        label_current_status.grid(row=1,
                                  column=1)

        label_current_status_txt = customtkinter.CTkLabel(master=frame,
                                                          text='Waiting for Work',
                                                          text_color='orange')
        label_current_status_txt.grid(row=2,
                                      column=1)

        label_input = customtkinter.CTkLabel(master=frame,
                                             text='INPUT (text or drag & drop)')
        label_input.grid(row=3,
                         column=1)

        self.input_TextBox = ScrolledText(
            frame,
            width=50,
            height=15,
            # selectmode=SINGLE,
            )
        self.input_TextBox.grid(row=4,
                           column=1)
        self.input_TextBox.drop_target_register(DND_FILES)
        self.input_TextBox.dnd_bind('<<Drop>>', self.input_text_handler)

    def input_text_handler(self,
                           event):
        received_path = event.data
        if received_path.startswith('{'):
            received_path = received_path[1:-1]
        self.input_TextBox.delete('1.0', END)
        self.input_TextBox.insert(END, received_path)

if __name__ == '__main__':

    customtkinter.set_appearance_mode("system")  # Modes: "System" (standard), "Dark", "Light"
    customtkinter.set_default_color_theme("green")  # Themes: "blue" (standard), "green", "dark-blue"

    # root = customtkinter.CTk()
    root = TkinterDnD.Tk()
    root.geometry("800x400")
    root.title("pyRoboCopy GUI")

    frame = customtkinter.CTkFrame(master=root)
    frame.pack(
        pady=5,
        padx=5,
        fill="both",
        expand=True
    )

    app = App(frame)

    root.mainloop()
