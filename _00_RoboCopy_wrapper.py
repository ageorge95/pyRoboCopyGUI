from typing import AnyStr,\
    Dict
from os import path

class RoboCopyWrapper():
    def __init__(self,
                 input: AnyStr,
                 output: AnyStr,
                 ipg: int = 0,
                 move: bool = False):

        self.input = input
        self.output = output
        self.ipg = ipg
        self.move = move

        # compute the arguments
        if path.isdir(self.input):
            self.input_path_str = self.input
            self.input_file_str = ''
        else:
            self.input_path_str = path.dirname(self.input)
            self.input_file_str = path.basename(self.input)

        self.output_path_str = self.output

        self.ipg_str = str(self.ipg)

        if self.move:
            self.move_str = r'/MOVE'
        else:
            self.move_str = ''

    def sanity_check(self) -> Dict:
        if not any([path.isdir(self.input), path.isfile(self.input)]):
            return {'success': False,
                    'reason': f"{self.input} is neither a file nor a dir"}
        if not path.isdir(self.output):
            return {'success': False,
                    'reason': f"{self.output} is not a dir"}
        return {'success': True,
                'reason': None}

    def return_full_CLI_call_str(self):
        return 'robocopy' + \
               f' "{self.input_path_str}"' + \
               f' "{self.output}"' + \
               (f' "{self.input_file_str}"' if self.input_file_str else '') + \
               f' {self.move_str}' + \
               f' /IPG {self.ipg_str}'
