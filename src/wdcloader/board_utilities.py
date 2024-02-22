"""This module contains all utility code for the boards"""

from time import sleep
from typing import final

from wdcloader.command_codes import Command_Code
from wdcloader.board_types import Board_Type

import serial

@final
class BoardUtilities:
    """
    This class collects utilty methods to interface directly with the boards
    or to extract information from data provided by the boards
    """

    @staticmethod
    def reset_board(ser: serial.Serial) -> None:
        """Resets the board via the DTR signal
        
        This seems to be ignored, at least for W65C02SXB and W65C816SXB.

        Args:
            ser (serial.Serial): Serial port connected to the board
        """    

        ser.setDTR(True)
        sleep(0.3)
        ser.setDTR(False)
        sleep(0.3)
        ser.setDTR(True)
        sleep(0.3)

    @staticmethod
    def send_command(ser: serial.Serial, cmd: Command_Code) -> None:
        """Send a command code to the board

        Args:
            ser (serial.Serial): Serial port connected to the board
            cmd (Command_Code): Command code to send

        Raises:
            RuntimeError: Raised when no response or an incorrect is received from the board
        """        
        ser.write(b'\x55\xAA')
        data = ser.read(1)

        if not data or data[0] != 0xCC:
            raise RuntimeError('No response from SXB --- Try to reset the board.')
        
        ser.write(cmd.value)

    # Info block
    # Offset:  W65C02  MyMENSCH W65C816
    # 00:      00      4d       00
    # 01:      7E      59       7E
    # 02:      00      4d       00
    # 03:      00      43       01          CPU Type
    # 04:      58      02       58          Board Type
    # 05:      00      00       00
    # 06:      7E      02       7E
    # 07:      00      00       00
    # 08:      00      00       00
    # 09:      80      F8       00
    # 10:      00      00       00
    # 11:      FA      FA       E4
    # 12:      7E      02       7E
    # 13:      00      00       00
    # 14:      00      00       00
    # 15:      7F      03       7F
    # 16:      00      00       00
    # 17:      FA      FA       E4
    # 18:      FF      FF       FF
    # 19:      00      00       00
    # 20:      00      00       00
    # 21:      7F      7F       7F
    # 22:      00      00       00
    # 23:      FF      FF       FF
    # 24:      7F      7F       7F
    # 25:      00      00       00
    # 26:      FF      90       FF
    # 27:      FF      7F       FF 
    @staticmethod
    def detect_board(info_data: bytes) -> Board_Type:
        """Detect the type of board connected

        Args:
            info_data (bytes): array of bytes containing the info data block

        Raises:
            ValueError: Raised when the passed data has the wrong length

        Returns:
            Board_Type: Detected board type based on the info data block
        """        
        if len(info_data) != 29:
            raise ValueError('The info data block should be exactly 29 bytes!')

        match info_data[3]:
            case 0x00:
                if info_data[4] == 0x58:
                    return Board_Type.W65C02SXB
            case 0x01:
                if info_data[4] == 0x58:
                    return Board_Type.W65C816SXB
            case 0x41 | 0x42 | 0x43:
                if info_data[0] == 0x4D and info_data[1] == 0x59 and info_data[2] == 0x4D:
                    return Board_Type(Board_Type.MyMENSCH_RevA.value + (info_data[3] - 0x41))
            case _:
                return Board_Type.UNKNOWN        
        
        return Board_Type.UNKNOWN


@final
class BoardCommands:
    """This class contains higher level board commands"""

    _STATE_ADDRESS: int = 0x7E00
    _STATE_SIZE: int = 16

    @staticmethod
    def read_info_data(ser: serial.Serial) -> bytes:
        """Read and return the info block from the board

        Args:
            ser (serial.Serial): Serial port connected to the board

        Returns:
            bytes: The info block, 29 bytes
        """        
        BoardUtilities.send_command(ser, Command_Code.GET_INFO)
        return ser.read(29)


    @staticmethod
    def read_memory(ser: serial.Serial, address: int, size: int) -> bytes:
        """Read 'size' bytes from target 'address' and return them as bytes.

        Args:
            ser (serial.Serial): Serial port connected to the board
            address (int): address (max 0xFFFFFF) of the memory to read
            size (int): number of bytes to read

        Returns:
            bytes: byte array containing the read data
        """        

        address = address & 0xFFFFFF # Trucate the address to 3 bytes
        size = size & 0xFFFF # Truncate the size to 2 bytes

        BoardUtilities.send_command(ser, Command_Code.READ_MEM)
        ser.write(address.to_bytes(length=3, byteorder='little', signed=False))
        ser.write(size.to_bytes(length=2, byteorder='little', signed=False))

        return ser.read(size)
    
    @staticmethod
    def write_memory(ser: serial.Serial, address: int, data: bytes) -> None:
        """Write the 'data' bytes (max 0xFFFF) directly into SXB's memory at 'address'

        Args:
            ser (serial.Serial): Serial port connected to the board
            address (int): Address (max 0xFFFFFF) of the memory to write
            data (bytes): data to write
        """        
        
        address = address & 0xFFFFFF # Trucate the address to 3 bytes
        data = data[:(len(data) & 0xFFFF)] # Truncate data size

        BoardUtilities.send_command(ser, Command_Code.WRITE_MEM)
        ser.write(address.to_bytes(length=3, byteorder='little', signed=False))
        ser.write(len(data).to_bytes(length=2, byteorder='little', signed=False))
        ser.write(data)

    @classmethod
    def execute_memory(cls, ser: serial.Serial, address: int, b_type: Board_Type) -> None:
        """Execute code in memory at 'address'

        Args:
            ser (serial.Serial): Serial port connected to the board
            address (int): Memory address at which to begin execution
            b_type (Board_Type): Board type

        Raises:
            ValueError: Raised when the board is of unknown type
        """        
        match b_type:
            case Board_Type.W65C02SXB | Board_Type.W65C816SXB:
                address = address & 0xFFFF # Trucate the address to 2 bytes
                data = [0] * cls._STATE_SIZE
                # Register A is in -> data[0], data[1]
                # Register X is in -> data[2], data[3]
                # Register Y is in -> data[4], data[5]
                addr_b = address.to_bytes(length=2, byteorder='little', signed=False)
                data[6] = addr_b[0] # Set the PC
                data[7] = addr_b[1]

                # DP seems (?) to be in data[8], data[9]
                
                data[10] = 0xFF # SP
                data[11] = 0x01

                data[12] = 0x34 # P (Status Register)
                data[13] = 0x01 # CPU Mode ? (0 -> 65816, 1 -> 6502)

                # PBR seems (?) to be in data[14]
                # DBR seems (?) to be in data[15]

                cls.write_memory(ser, cls._STATE_ADDRESS, bytes(data))
                BoardUtilities.send_command(ser, Command_Code.EXEC_DEBUG)
            case Board_Type.MyMENSCH_RevA | Board_Type.MyMENSCH_RevB | Board_Type.MyMENSCH_RevC:
                address = address & 0xFFFFFF # Trucate the address to 3 bytes
                BoardUtilities.send_command(ser, Command_Code.EXEC_MEM)
                ser.write(address.to_bytes(length=3, byteorder='little', signed=False))
            case _:
                raise ValueError('Cannot execute memory on an unknown board!')
            
    @classmethod
    def read_state(cls, ser: serial.Serial, b_type: Board_Type) -> bytes:
        """Helper to read the 16 bytes at memory address 0x7E00 to retrieve CPU state

        Args:
            ser (serial.Serial): Serial port connected to the board
            b_type (Board_Type): Detected board type

        Raises:
            ValueError: Raised when executed on an unsupported/unknown board

        Returns:
            bytes: 16 bytes containing the CPU state
        """        
        match b_type:
            case Board_Type.W65C02SXB | Board_Type.W65C816SXB:
                return cls.read_memory(ser, cls._STATE_ADDRESS, cls._STATE_SIZE)
            case _:
                raise ValueError(f'Cannot read state on board type {b_type.name}')

