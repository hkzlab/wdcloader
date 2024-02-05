"""This module contains the codes for all supported board commands"""

from enum import Enum

class Command_Codes(Enum):
    SYNC = 0
    ECHO = 1
    WRITE_MEM = 2
    READ_MEM = 3
    GET_INFO = 4
    EXEC_DEBUG = 5
    EXEC_MEM = 6
    WRITE_FLASH = 7
    READ_FLASH = 8
    CLEAR_FLASH = 9
    CHECK_FLASH = 10
    EXEC_FLASH = 11
