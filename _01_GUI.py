import sys
sys.path.insert(0, 'CustomTkinter')

from _00_RoboCopy_wrapper import RoboCopyWrapper
from CustomTkinter import customtkinter
from tkinter import *
from tkinter import ttk
from tkinterdnd2 import *
from tkinter.scrolledtext import ScrolledText
from os import system

class App():
    def __init__(self,
                 frame):

        # ################################
        label_current_status = customtkinter.CTkLabel(master=frame,
                                                      text='Current Status')
        label_current_status.grid(row=1,
                                  column=1,
                                  columnspan=3)

        # ################################
        self.label_current_status_txt = customtkinter.CTkLabel(master=frame,
                                                               text='Waiting for Work',
                                                               text_color='orange')
        self.label_current_status_txt.grid(row=2,
                                           column=1,
                                           columnspan=3)

        # ################################
        horizontal_line_1 = ttk.Separator(master=frame,
                                          orient='horizontal')
        horizontal_line_1.grid(row=3,
                               column=1,
                               columnspan=3,
                               sticky='EW',
                               pady=5)

        # ################################
        label_input = customtkinter.CTkLabel(master=frame,
                                             text='INPUT (text or drag & drop)')
        label_input.grid(row=4,
                         column=1,
                         columnspan=3)
        self.input_TextBox = ScrolledText(
            frame,
            width=95,
            height=4,
            )
        self.input_TextBox.grid(row=5,
                                column=1,
                                columnspan=3)
        self.input_TextBox.drop_target_register(DND_FILES)
        self.input_TextBox.dnd_bind('<<Drop>>', self.input_text_handler)

        # ################################
        label_output = customtkinter.CTkLabel(master=frame,
                                              text='OUTPUT (text or drag & drop)')
        label_output.grid(row=6,
                          column=1,
                          columnspan=3)
        self.output_TextBox = ScrolledText(
            frame,
            width=95,
            height=4
            )
        self.output_TextBox.grid(row=7,
                                 column=1,
                                 columnspan=3)
        self.output_TextBox.drop_target_register(DND_FILES)
        self.output_TextBox.dnd_bind('<<Drop>>', self.output_text_handler)

        # ################################
        horizontal_line_2 = ttk.Separator(master=frame,
                                          orient='horizontal')
        horizontal_line_2.grid(row=8,
                               column=1,
                               columnspan=3,
                               sticky='EW',
                               pady=5)

        # ################################
        self.move_checkbox_variable = customtkinter.BooleanVar()
        self.move_checkbox = customtkinter.CTkCheckBox(master=frame,
                                                       text='Move ?',
                                                       variable=self.move_checkbox_variable)
        self.move_checkbox.grid(row=9,
                                column=1)

        ipg_value_label = customtkinter.CTkLabel(master=frame,
                                                      text='InterPacketGap value (speed_limiter)')
        ipg_value_label.grid(row=9,
                             column=2,
                             sticky='E')

        self.ipg_value_combobox = customtkinter.CTkComboBox(master=frame,
                                                            values=[
                                                                '0__MAX MB/s',
                                                                '25__30 MB/s',
                                                                '30__22 MB/s',
                                                                '40__20 MB/s',
                                                                '50__14.5 MB/s'
                                                            ])
        self.ipg_value_combobox.grid(row=9,
                                     column=3,
                                     sticky='W')

        # ################################
        horizontal_line_3 = ttk.Separator(master=frame,
                                          orient='horizontal')
        horizontal_line_3.grid(row=10,
                               column=1,
                               columnspan=3,
                               sticky='EW',
                               pady=5)

        # ################################
        self.generate_CLI_args_button = customtkinter.CTkButton(master=frame,
                                                                text='Generate CLI code',
                                                                command=lambda : self.launch_robocopy(launch=False))
        self.generate_CLI_args_button.grid(row=11,
                                           column=1)

        self.generate_CLI_execute_button = customtkinter.CTkButton(master=frame,
                                                                   text='Generate CLI code & Execute',
                                                                   command = lambda: self.launch_robocopy(launch=True)
        )
        self.generate_CLI_execute_button.grid(row=11,
                                              column=3)

        # ################################
        horizontal_line_3 = ttk.Separator(master=frame,
                                          orient='horizontal')
        horizontal_line_3.grid(row=12,
                               column=1,
                               columnspan=3,
                               sticky='EW',
                               pady=5)

        # ################################
        label_CLI_args = customtkinter.CTkLabel(master=frame,
                                               text='CLI args (str):')
        label_CLI_args.grid(row=13,
                            column=1,
                            columnspan=3)
        self.TextBox_CLI_args_value = ScrolledText(frame,
            width=95,
            height=4,
            state='disabled'
        )
        self.TextBox_CLI_args_value.grid(row=14,
                                  column=1,
                                  columnspan=3)

    def input_text_handler(self,
                           event):
        received_path = event.data
        if received_path.startswith('{'):
            received_path = received_path[1:-1]
        self.input_TextBox.delete('1.0', END)
        self.input_TextBox.insert(END, received_path)

    def output_text_handler(self,
                           event):
        received_path = event.data
        if received_path.startswith('{'):
            received_path = received_path[1:-1]
        self.output_TextBox.delete('1.0', END)
        self.output_TextBox.insert(END, received_path)

    def launch_robocopy(self,
                        launch: bool):
        robocopy_wrapper = RoboCopyWrapper(input=self.input_TextBox.get('1.0', END).strip(),
                                           output=self.output_TextBox.get('1.0', END).strip(),
                                           move=self.move_checkbox_variable.get(),
                                           ipg=int(self.ipg_value_combobox.get().split('__')[0]))
        # sanity checks
        sanity_check = robocopy_wrapper.sanity_check()
        if not sanity_check['success']:
            self.label_current_status_txt.configure({'text': f"SANITY CHECK FAILED: {sanity_check['reason']}",
                                                     'fg': 'red'})

        else:
            self.label_current_status_txt.configure({'text': f"SANITY CHECK PASSED",
                                                     'fg': 'green'})

            CLI_args_str = robocopy_wrapper.return_full_CLI_call_str()

            self.TextBox_CLI_args_value.configure(state='normal')
            self.TextBox_CLI_args_value.delete('1.0', END)
            self.TextBox_CLI_args_value.insert(END, CLI_args_str)
            self.TextBox_CLI_args_value.configure(state='disabled')

            if launch:
                self.label_current_status_txt.configure({'text': f"RoboCopy launched",
                                                         'fg': 'green'})
                rbcp_proc = system(f"start /wait cmd /c {CLI_args_str}")
                self.label_current_status_txt.configure({'text': f"RoboCopy finished, exit code {rbcp_proc}",
                                                         'fg': 'green'})

if __name__ == '__main__':

    customtkinter.set_appearance_mode("system")  # Modes: "System" (standard), "Dark", "Light"
    customtkinter.set_default_color_theme("green")  # Themes: "blue" (standard), "green", "dark-blue"

    # root = customtkinter.CTk()
    root = TkinterDnD.Tk()
    root.geometry("795x460")
    root.title("pyRoboCopy GUI")
    root.resizable(width=False,
                   height=False)

    frame = customtkinter.CTkFrame(master=root)
    frame.pack(
        pady=5,
        padx=5,
        fill="both",
        expand=True
    )

    app = App(frame)

    root.mainloop()
