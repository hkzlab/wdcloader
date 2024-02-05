"""This module contains all utility code for the boards"""

from time import sleep
from typing import final

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