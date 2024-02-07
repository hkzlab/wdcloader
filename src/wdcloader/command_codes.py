"""This module contains the codes for all supported board commands"""

from enum import Enum

class Command_Code(Enum):
    SYNC = b'\x00'
    ECHO = b'\x01'
    WRITE_MEM = b'\x02'
    READ_MEM = b'\x03'
    GET_INFO = b'\x04'
    EXEC_DEBUG = b'\x05'
    EXEC_MEM = b'\x06'
    WRITE_FLASH = b'\x07'
    READ_FLASH = b'\x08'
    CLEAR_FLASH = b'\x09'
    CHECK_FLASH = b'\x0A'
    EXEC_FLASH = b'\x0B'
