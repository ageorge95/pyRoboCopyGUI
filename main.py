import sys
import os
from threading import Thread
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QLabel,
    QTextEdit, QPushButton, QCheckBox, QComboBox,
    QFrame, QWidget, QHBoxLayout
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
                 ipg: int = 0,
                 move: bool = False):

        self.input = input
        self.output = output
        self.ipg = ipg
        self.move = move

        # compute the arguments
        if os.path.isdir(self.input):
            self.input_path_str = self.input
            self.input_file_str = ''
        else:
            self.input_path_str = os.path.dirname(self.input)
            self.input_file_str = os.path.basename(self.input)

        self.output_path_str = self.output

        self.ipg_str = str(self.ipg)

        if self.move:
            if os.path.isdir(self.input):
                self.move_str = r'/MOVE'
            else:
                self.move_str = r'/mov'
        else:
            self.move_str = ''

    def sanity_check(self) -> dict:
        if not any([os.path.isdir(self.input), os.path.isfile(self.input)]):
            return {'success': False,
                    'reason': f"INPUT {self.input} is neither a file nor a dir"}
        if not os.path.isdir(os.path.dirname(self.output)):
            return {'success': False,
                    'reason': f"OUTPUT {self.output} is not a dir"}
        return {'success': True,
                'reason': None}

    def return_full_CLI_call_str(self):
        return 'robocopy' + \
            (' /E' if os.path.isdir(self.input) else '') + \
            f' "{self.input_path_str}"' + \
            f' "{self.output}"' + \
            (f' "{self.input_file_str}"' if self.input_file_str else '') + \
            f' {self.move_str}' + \
            f' /IPG:{self.ipg_str}'

def get_running_path(relative_path):
    if '_internal' in os.listdir():
        return os.path.join('_internal', relative_path)
    else:
        return relative_path

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("pyRoboCopy GUI v" + open(get_running_path('version.txt')).read())
        self.setGeometry(200, 200, 800, 500)
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

        # Move Checkbox and IPG Combobox
        options_layout = QHBoxLayout()
        self.move_checkbox = QCheckBox("Move?")
        self.ipg_label = QLabel("InterPacketGap value (speed_limiter):")
        self.ipg_combobox = QComboBox()
        self.ipg_combobox.addItems([
            "0__MAX MB/s",
            "25__30 MB/s",
            "30__22 MB/s",
            "40__20 MB/s",
            "50__14.5 MB/s",
        ])
        options_layout.addWidget(self.move_checkbox)
        options_layout.addStretch()
        options_layout.addWidget(self.ipg_label)
        options_layout.addWidget(self.ipg_combobox)
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
                                           move=self.move_checkbox.isChecked(),
                                           ipg=int(self.ipg_combobox.currentText().split('__')[0]))
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
            result_code = os.system(f"start /wait cmd /c {cli_args_str}")
            # noinspection PyTypeChecker
            QMetaObject.invokeMethod(self.status_text, "setText",
                                     Q_ARG(str, f"RoboCopy finished, exit code {result_code}, waiting for work ..."))
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
