import sys
import os
import subprocess
from threading import Thread
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QLabel,
    QTextEdit, QPushButton, QCheckBox, QComboBox,
    QFrame, QWidget, QHBoxLayout, QLineEdit
)
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QIcon
from PySide6.QtCore import QMetaObject, Q_ARG

class DragDropTextEdit(QTextEdit):
    """Custom QTextEdit with drag-and-drop support."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            self.setPlainText(urls[0].toLocalFile())

class RoboCopyWrapper():
    def __init__(self,
                 input: str,
                 output: str,
                 iorate: int = 0,
                 move: bool = False,
                 keep_timestamps: bool = False,
                 mirror: bool = False,
                 mt: int = 0,
                 restartable: bool = False,
                 huge_files: bool = False):

        self.input = input
        self.output = output
        self.iorate = iorate
        self.move = move
        self.keep_timestamps = keep_timestamps
        self.mirror = mirror
        self.mt = mt
        self.restartable = restartable
        self.huge_files = huge_files

        # compute the arguments
        if os.path.isdir(self.input):
            self.input_path_str = self.input
            self.input_file_str = ''
        else:
            self.input_path_str = os.path.dirname(self.input)
            self.input_file_str = os.path.basename(self.input)

        self.output_path_str = self.output

        if self.move:
            if os.path.isdir(self.input):
                self.move_str = r'/MOVE'
            else:
                self.move_str = r'/mov'
        else:
            self.move_str = ''

    def sanity_check(self) -> dict:
        if not any([os.path.isdir(self.input), os.path.isfile(self.input)]):
            return {
                'success': False,
                'reason': f"INPUT {self.input} is neither a file nor a dir"
            }
        if not os.path.isdir(os.path.dirname(self.output)):
            return {
                'success': False,
                'reason': f"OUTPUT {self.output} is not a dir"
            }
        if self.mirror and (os.path.isfile(self.input) or os.path.isfile(self.output)):
            return {
                'success': False,
                'reason': f"Cannot mirror files, only directories !"
            }
        return {'success': True,
                'reason': None}

    def return_full_CLI_call_str(self):
        return 'robocopy' + \
            (' /E' if os.path.isdir(self.input) else '') + \
            f' "{self.input_path_str}"' + \
            f' "{self.output}"' + \
            (f' "{self.input_file_str}"' if self.input_file_str else '') + \
            f' {self.move_str}' + \
            ' /COPY:DA' + ('T' if self.keep_timestamps else '') + \
            (' /MIR' if self.mirror else '') + \
            (' /Z' if self.restartable else '') + \
            (f' /MT:{self.mt}' if self.mt else '') + \
            (' /J' if self.huge_files else '') + \
            (f' /IORate:{self.iorate}M' if self.iorate else '')

def get_running_path(relative_path):
    if '_internal' in os.listdir():
        return os.path.join('_internal', relative_path)
    else:
        return relative_path

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("pyRoboCopy GUI v" + open(get_running_path('version.txt')).read())
        self.setGeometry(200, 200, 1000, 500)
        self.setWindowIcon(QIcon(get_running_path('icon.ico')))

        # Main layout
        main_widget = QWidget(self)
        main_layout = QVBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        # Current Status
        self.status_label = QLabel("Current Status")
        self.status_text = QLabel("Waiting for Work")
        self.status_text.setStyleSheet("color: orange;")
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(self.status_text)

        # Separator
        main_layout.addWidget(self._create_separator())

        # Input Section
        self.input_label = QLabel("INPUT (text or drag & drop)")
        self.input_textbox = DragDropTextEdit()
        main_layout.addWidget(self.input_label)
        main_layout.addWidget(self.input_textbox)

        # Output Section
        self.output_label = QLabel("OUTPUT (text or drag & drop)")
        self.output_textbox = DragDropTextEdit()
        main_layout.addWidget(self.output_label)
        main_layout.addWidget(self.output_textbox)

        # Separator
        main_layout.addWidget(self._create_separator())

        # Options
        options_layout = QHBoxLayout()

        self.main_action_selection_label = QLabel("Main action:")
        self.main_action_selection_combobox = QComboBox()
        self.main_action_selection_combobox.addItems(["Copy", "Move"])

        self.keep_timestamps_label = QLabel("Keep Timestamps:")
        self.keep_timestamps_combobox = QComboBox()
        self.keep_timestamps_combobox.addItems(["No", "Yes"])

        self.mirror_selection_label = QLabel("Mirror:")
        self.mirror_selection_combobox = QComboBox()
        self.mirror_selection_combobox.addItems(["No", "Yes"])

        self.restartable_selection_label = QLabel("Restartable:")
        self.restartable_selection_combobox = QComboBox()
        self.restartable_selection_combobox.addItems(["No", "Yes"])

        self.multithreading_selection_label = QLabel("MultiThreading:")
        self.multithreading_selection_combobox = QComboBox()
        self.multithreading_selection_combobox.addItems(['0', '2', '5', '10', '15', '20'])

        self.huge_files_selection_label = QLabel("Huge Files:")
        self.huge_files_selection_combobox = QComboBox()
        self.huge_files_selection_combobox.addItems(["No", "Yes"])

        self.speed_limit_label = QLabel("Total I/O [MB]:")
        self.speed_limit_input = QLineEdit()
        self.speed_limit_input.setPlaceholderText('unlimited')

        options_layout.addWidget(self.main_action_selection_label)
        options_layout.addWidget(self.main_action_selection_combobox)
        options_layout.addStretch()
        options_layout.addWidget(self.keep_timestamps_label)
        options_layout.addWidget(self.keep_timestamps_combobox)
        options_layout.addStretch()
        options_layout.addWidget(self.mirror_selection_label)
        options_layout.addWidget(self.mirror_selection_combobox)
        options_layout.addStretch()
        options_layout.addWidget(self.restartable_selection_label)
        options_layout.addWidget(self.restartable_selection_combobox)
        options_layout.addStretch()
        options_layout.addWidget(self.multithreading_selection_label)
        options_layout.addWidget(self.multithreading_selection_combobox)
        options_layout.addStretch()
        options_layout.addWidget(self.huge_files_selection_label)
        options_layout.addWidget(self.huge_files_selection_combobox)
        options_layout.addStretch()
        options_layout.addWidget(self.speed_limit_label)
        options_layout.addWidget(self.speed_limit_input)
        main_layout.addLayout(options_layout)

        # Separator
        main_layout.addWidget(self._create_separator())

        # Buttons
        buttons_layout = QHBoxLayout()
        self.generate_button = QPushButton("Generate CLI code")
        self.execute_button = QPushButton("Generate CLI code & Execute")
        self.generate_button.clicked.connect(lambda: self.launch_robocopy(launch=False))
        self.execute_button.clicked.connect(lambda: self.launch_robocopy(launch=True))
        buttons_layout.addWidget(self.generate_button)
        buttons_layout.addWidget(self.execute_button)
        main_layout.addLayout(buttons_layout)

        # Separator
        main_layout.addWidget(self._create_separator())

        # CLI Args Section
        self.cli_args_label = QLabel("CLI args (str):")
        self.cli_args_textbox = QTextEdit()
        self.cli_args_textbox.setReadOnly(True)
        main_layout.addWidget(self.cli_args_label)
        main_layout.addWidget(self.cli_args_textbox)

    def _create_separator(self):
        """Creates a horizontal line (separator)."""
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        return line

    def launch_robocopy(self, launch: bool):
        Thread(target=self._launch_robocopy_slave, args=(launch,)).start()

    def _launch_robocopy_slave(self, launch: bool):
        robocopy_wrapper = RoboCopyWrapper(input=self.input_textbox.toPlainText().strip(),
                                           output=self.output_textbox.toPlainText().strip(),
                                           move=True if self.main_action_selection_combobox.currentText() == 'Move' else False,
                                           keep_timestamps=True if self.keep_timestamps_combobox.currentText() == 'Yes' else False,
                                           iorate=int(self.speed_limit_input.text())
                                                if (self.speed_limit_input.text() != 'unlimited' and self.speed_limit_input.text().isdigit())
                                                else 0,
                                           mirror=True if self.mirror_selection_combobox.currentText() == 'Yes' else False,
                                           mt=int(self.multithreading_selection_combobox.currentText()),
                                           restartable=True if self.restartable_selection_combobox.currentText() == 'Yes' else False,
                                           huge_files=True if self.huge_files_selection_combobox.currentText() == 'Yes' else False)
        # Sanity checks
        sanity_check = robocopy_wrapper.sanity_check()
        if not sanity_check['success']:
            # noinspection PyTypeChecker
            QMetaObject.invokeMethod(self.status_text, "setText",
                                     Q_ARG(str, f"SANITY CHECK FAILED: {sanity_check['reason']}"))
            # noinspection PyTypeChecker
            QMetaObject.invokeMethod(self.status_text, "setStyleSheet",
                                     Q_ARG(str, "color: red;"))
            return

        # noinspection PyTypeChecker
        QMetaObject.invokeMethod(self.status_text, "setText",
                                 Q_ARG(str, "SANITY CHECK PASSED"))
        # noinspection PyTypeChecker
        QMetaObject.invokeMethod(self.status_text, "setStyleSheet",
                                 Q_ARG(str, "color: green;"))

        cli_args_str = robocopy_wrapper.return_full_CLI_call_str()

        # Thread-safe GUI update for the CLI args textbox
        # noinspection PyTypeChecker
        QMetaObject.invokeMethod(self.cli_args_textbox, "setPlainText",
                                 Q_ARG(str, cli_args_str))

        if launch:
            # Disable the execute button during execution
            # noinspection PyTypeChecker
            QMetaObject.invokeMethod(self.execute_button, "setDisabled", Q_ARG(bool, True))
            # noinspection PyTypeChecker
            QMetaObject.invokeMethod(self.status_text, "setText",
                                     Q_ARG(str, "RoboCopy launched"))
            # noinspection PyTypeChecker
            QMetaObject.invokeMethod(self.status_text, "setStyleSheet",
                                     Q_ARG(str, "color: green;"))
            result = subprocess.run(f"start /wait cmd /c {cli_args_str}", shell=True)
            # noinspection PyTypeChecker
            QMetaObject.invokeMethod(self.status_text, "setText",
                                     Q_ARG(str, f"RoboCopy finished, exit code {result.returncode}, waiting for work ..."))
            # noinspection PyTypeChecker
            QMetaObject.invokeMethod(self.status_text, "setStyleSheet",
                                     Q_ARG(str, "color: orange;"))
            # noinspection PyTypeChecker
            QMetaObject.invokeMethod(self.execute_button, "setDisabled", Q_ARG(bool, False))

        else:
            # noinspection PyTypeChecker
            QMetaObject.invokeMethod(self.status_text, "setText",
                                     Q_ARG(str, "CLI code created, waiting for work ..."))
            # noinspection PyTypeChecker
            QMetaObject.invokeMethod(self.status_text, "setStyleSheet",
                                     Q_ARG(str, "color: orange;"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
