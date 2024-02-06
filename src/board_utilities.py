"""This module contains all utility code for the boards"""

from time import sleep
from typing import final

from command_codes import Command_Code

import serial

@final
class BoardUtilities:
    """This class collects utilty methods to interface with the boards"""

    @staticmethod
    def reset_board(ser: serial.Serial) -> None:
        """Reset the board"""
        ser.setDTR(True)
        sleep(0.3)
        ser.setDTR(False)
        sleep(0.3)
        ser.setDTR(True)
        sleep(0.3)

    @staticmethod
    def send_command(ser: serial.Serial, cmd: Command_Code) -> None:
        ser.write(b'\x55\xAA')
        data = ser.read(1)

        if not data:
            raise RuntimeError('No response from SXB --- Try to reset the board.')
        
        ser.write(cmd.value)
