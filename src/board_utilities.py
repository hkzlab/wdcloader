"""This module contains all utility code for the boards"""

from time import sleep
from typing import final

from command_codes import Command_Code
from board_types import Board_Type

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

    @staticmethod
    def detect_board(info_data: bytes) -> Board_Type:
        raise NotImplementedError

@final
class BoardCommands:
    """This class contains high level board commands"""

    @staticmethod
    def read_memory(ser: serial.Serial, address: int, size: int) -> bytes:
        """
        Read 'size' bytes from target 'address' and return them as bytes.

        :param serial.Serial ser: Serial port connected to the board
        :param int address: address (max 0xFFFFFF) of the memory to read
        :param int size: number of bytes to read
        :return: read bytes
        """

        address = address & 0xFFFFFF # Trucate the address to 3 bytes
        size = size & 0xFFFF # Truncate the size to 2 bytes

        BoardUtilities.send_command(ser, Command_Code.READ_MEM)
        ser.write(address.to_bytes(length=3, byteorder='little', signed=False))
        ser.write(size.to_bytes(length=2, byteorder='little', signed=False))

        return ser.read(size)
    
    @staticmethod
    def write_memory(ser: serial.Serial, address: int, data: bytes) -> None:
        """
        Write the 'data' bytes (max 0xFFFF) directly into SXB's memory at 'address'

        :param serial.Serial ser: Serial port connected to the board
        :param int address: address (max 0xFFFFFF) of the memory to write
        :param bytes data: data to write
        """
        
        address = address & 0xFFFFFF # Trucate the address to 3 bytes
        data = data[:(len(data) & 0xFFFF)] # Truncate data size

        BoardUtilities.send_command(ser, Command_Code.WRITE_MEM)
        ser.write(address.to_bytes(length=3, byteorder='little', signed=False))
        ser.write(len(data).to_bytes(length=2, byteorder='little', signed=False))
        ser.write(data)



