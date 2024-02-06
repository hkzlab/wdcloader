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

    # Info block
    # Offset:  W65C02  W65C165 W65C816
    # 00:      00      4d      00
    # 01:      7E      59      7E
    # 02:      00      4d      00
    # 03:      00      43      01          CPU Type
    # 04:      58      02      58          Board Type
    # 05:      00      00      00
    # 06:      7E      02      7E
    # 07:      00      00      00
    # 08:      00      00      00
    # 09:      80      F8      00
    # 10:      00      00      00
    # 11:      FA      FA      E4
    # 12:      7E      02      7E
    # 13:      00      00      00
    # 14:      00      00      00
    # 15:      7F      03      7F
    # 16:      00      00      00
    # 17:      FA      FA      E4
    # 18:      FF      FF      FF
    # 19:      00      00      00
    # 20:      00      00      00
    # 21:      7F      7F      7F
    # 22:      00      00      00
    # 23:      FF      FF      FF
    # 24:      7F      7F      7F
    # 25:      00      00      00
    # 26:      FF      90      FF
    # 27:      FF      7F      FF 
    @staticmethod
    def detect_board(info_data: bytes) -> Board_Type:
        if len(info_data) != 28:
            raise ValueError('The info data block should be exactly 28 bytes!')

        match info_data[3]:
            case 0x00:
                if info_data[4] == 0x58:
                    return Board_Type.W65C02SXB
            case 0x01:
                if info_data[4] == 0x58:
                    return Board_Type.W65C816SXB
            case 0x41 | 0x42 | 0x43:
                if info_data[0] == 0x4D and info_data[1] == 0x59 and info_data[2] == 0x4D:
                    return Board_Type.W65C165SXB_A + (info_data[3] - 0x41)
            case _:
                return Board_Type.UNKNOWN        
        
        return Board_Type.UNKNOWN


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

    @classmethod
    def execute_memory(cls, ser: serial.Serial, address: int, b_type: Board_Type) -> None:
        match b_type:
            case Board_Type.W65C02SXB | Board_Type.W65C816SXB:
                address = address & 0xFFFF # Trucate the address to 2 bytes
                data = bytes([0] * 16)
                # Register A is in -> data[0], data[1]
                # Register B is in -> data[2], data[3]
                # Register C is in -> data[4], data[5]
                addr_b = address.to_bytes(length=2, byteorder='little', signed=False)
                data[6] = addr_b[0] # Set the PC
                data[7] = addr_b[1]

                # DP seems (?) to be in data[8], data[9]
                data[10] = 0xFF # SP
                data[11] = 0x00

                data[12] = 0x34 # P
                data[13] = 0x01

                # PBR seems (?) to be in data[14]
                # DBR seems (?) to be in data[15]

                cls.write_memory(ser, 0x7E00, data)
                BoardUtilities.send_command(ser, Command_Code.EXEC_DEBUG)
            case Board_Type.W65C165SXB_A | Board_Type.W65C165SXB_B | Board_Type.W65C165SXB_C:
                address = address & 0xFFFFFF # Trucate the address to 3 bytes
                BoardUtilities.send_command(ser, Command_Code.EXEC_MEM)
                ser.write(address.to_bytes(length=3, byteorder='little', signed=False))
            case _:
                raise ValueError('Cannot execute memory on an unknown board!')

