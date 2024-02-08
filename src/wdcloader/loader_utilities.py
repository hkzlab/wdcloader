"""This module contains utility code for the loader"""

from typing import final, List
import struct

import serial
from serial.tools.list_ports import comports
from serial.tools.miniterm import Miniterm

from wdcloader.board_utilities import BoardCommands
from wdcloader.board_types import Board_Type

@final
class LoaderUtilities:
    """
    This class contains higher level utilities for the loader, to support
    various types of inbound and outboud data.
    """

    @staticmethod
    def load_records(ser: serial.Serial, filename: str) -> None:
        """Load data from 'filename' in SREC format into the board's memory.

        Args:
            ser (serial.Serial): Serial port connected to the board
            filename (str): path to the file containing the data in SREC format
        """        

        file = open(filename, 'r')
        total: int = 0

        # See https://en.wikipedia.org/wiki/SREC_(file_format)
        try:
            for line in file:
                count: int = 0
                if line.startswith('S1'): # 16 bit address record
                    count = int(line[2:4], 16) - 3
                    address = int(line[4:8], 16)
                    print(f'Loading S1 record of size {count} at address {'0x%.4X' % address} ...')
                    data = bytearray.fromhex(line[8:(count*2)+8])
                    # Ignore the checksum for now
                    BoardCommands.write_memory(ser, address, data)
                elif line.startswith('S2'): # 24 bit address record
                    count = int(line[2:4], 16) - 4
                    address = int(line[4:10], 16)
                    print(f'Loading S2 record of size {count} at address {'0x%.6X' % address} ...')
                    data = bytearray.fromhex(line[10:(count*2)+10])
                    # Ignore the checksum for now
                    BoardCommands.write_memory(ser, address, data)

                total = total + count
        finally:
            file.close()

        print(f'Loaded {total} bytes from {filename}.')

    @staticmethod
    def load_binary(ser: serial.Serial, filename: str) -> None:
        """Load data from 'filename' in WDC's binary format into the board's memory.

        Args:
            ser (serial.Serial): Serial port connected to the board
            filename (str): path to the file containing the data in WDC's binary format

        Raises:
            ValueError: Raised when the file is in the wrong format
        """

        header_fmt = '<BBBBBB'
        header_size = struct.calcsize(header_fmt)
        header_unpack = struct.Struct(header_fmt).unpack_from

        file = open(filename, 'rb')
        total: int = 0

        try:
            start = file.read(1)
            if not start or start[0] != 0x5A:
                raise ValueError('The file is not in WDC\'s format!')
            
            while True:
                header = file.read(header_size)
                if not header or len(header) != header_size: break
                a1, a2, a3, s1, s2, s3 = header_unpack(header)
                address = a1 | a2 << 8 | a3 << 16
                size = s1 | s2 << 8 | s3 << 16

                data = file.read(size)
                if not data or len(data) != size: break
                
                print(f'Loading WDC binary record of size {size} at address {'0x%.6X' % address} ...')
                BoardCommands.write_memory(ser, address, data)

                total = total + size
        finally:
            file.close()

        print(f'Loaded {total} bytes from {filename}.')

    @staticmethod
    def load_raw_binary(ser: serial.Serial, address: int, filename: str) -> None:
        """Load data from 'filename' in raw binary format into the board's memory at specified address.

        Args:
            ser (serial.Serial): Serial port connected to the board
            address (int): address at which to load
            filename (str): path to the file containing the data in raw binary format
        """

        address = address & 0xFFFFFF

        file = open(filename, 'rb')
        total: int = 0

        try:
            while True:
                data = file.read(64)

                if not data: break

                BoardCommands.write_memory(ser, address, data)

                address = address + len(data)
                total = total + len(data)
        finally:
            file.close()

        print(f'Loaded {total} bytes from {filename}.')

    @staticmethod
    def save_binary(address:int, data: bytes, filename: str) -> None:
        """Save binary data to a file in WDC's format

        Args:
            address (int): Source address of the data
            data (bytes): data to be saved
            filename (str): path to destination file

        Raises:
            IOError: Raised when failing to write to the file
        """

        file = open(filename, 'wb')
        try:
            data_len = len(data)
            header: bytes = bytes([0x5A,
                                   address & 0xFF,
                                   (address >> 8) & 0xFF,
                                   (address >> 16) & 0xFF,
                                   data_len & 0xFF,
                                   (data_len >> 8) & 0xFF,
                                   (data_len >> 16) & 0xFF])
            
            if file.write(header) != len(header):
                raise IOError('Unable to write the header to the file')
            
            if file.write(data) != data_len:
                raise IOError('Unable to write the data to the file')
        finally:
            file.close()

    @staticmethod
    def save_records(address: int, data: bytes, filename: str) -> None:
        """Save binary data to a file in SREC format

        Args:
            address (int): Source address of the data
            data (bytes): data to be saved
            filename (str): path to destination file
        """        
        file = open(filename, 'w')
        try:
            data_len = len(data)
            offset = 0

            while data_len:
                count = 32 if data_len > 32 else data_len
                check = count + 4

                file.write('S2')
                file.write('%.2x' % check)
                file.write('%.6x' % address)

                check = check + address & 0xFF
                check = check + (address >> 8) & 0xFF
                check = check + (address >> 16) & 0xFF

                for idx in range(count):
                    value = data[offset + idx]
                    file.write('%.2x' % value)
                    check = check + value

                offset = offset + count
                check = 0xFF - (check & 0xFF)
                file.write('%.2x\n' % check)

                data_len = data_len - count
                address = address + count
        finally:
            file.close()

    @staticmethod
    def print_state(ser: serial.Serial, b_type: Board_Type) -> None:
        """Read and print the CPU state

        Args:
            ser (serial.Serial): Serial port connected to the board
            b_type (Board_Type): Detected board type

        Raises:
            IOError: Raised when an incorrect number of bytes is read
        """        
        state_fmt = '<HHHHHHBBBB'
        state_size = struct.calcsize(state_fmt)
        state_unpack = struct.Struct(state_fmt).unpack_from

        state_data = BoardCommands.read_state(ser, b_type)

        if len(state_data) != state_size:
            raise IOError(f'Somehow we read {len(state_data)} instead of the correct {state_size} state bytes')
        
        # Unpack the response.
        # Note that the position of the registers are taken from Andrew Jacob's code
        # and I'm not really sure they're correct
        r_A, r_X, r_Y, r_PC, r_DP, r_SP, r_P, cpu_mode, r_PBR, r_DBR = state_unpack(state_data)

        str_component: List[str] = []
        str_component.append(f'A   ->\t{'%.4X' % r_A}')
        str_component.append(f'X   ->\t{'%.4X' % r_X}')
        str_component.append(f'Y   ->\t{'%.4X' % r_Y}')
        str_component.append(f'PC  ->\t{'%.4X' % r_PC}')
        str_component.append(f'DP  ->\t{'%.4X' % r_DP}')
        str_component.append(f'SP  ->\t{'%.4X' % r_SP}')
        str_component.append(f'P   ->\t{'%.2X' % r_P}')
        str_component.append(f'CPU ->\t{'%.2X' % cpu_mode}')
        str_component.append(f'PBR ->\t{'%.2X' % r_PBR}')
        str_component.append(f'DBR ->\t{'%.2X' % r_DBR}')

        print(*str_component, sep='\n', end='\n\n')


    @staticmethod
    def print_memory(address:int, data: bytes) -> None:
        """Format and print memory as hexadecimal and ASCII values

        Args:
            address (int): Address at which the memory starts
            data (bytes): data to print
        """        
        data_len = len(data)
        offset = 0

        while data_len > 0:
            str_component: List[str] = []

            # Address
            str_component.append('%.6X ' % address)
            str_component.append('| ')

            data_line = data[offset:offset+16]
            counter = 0

            # Hex representation of data
            for b in data_line:
                str_component.append('%.2x ' % b)
                counter = counter + 1
            for i in range(counter, 16):
                str_component.append('.. ')

            str_component.append('| ')

            # ASCII representation of data
            counter = 0
            for b in data_line:
                if b >= 0x20 and b <= 0x7E:
                    str_component.append('%c' % b)
                else:
                    str_component.append('.')
                counter = counter + 1
            for i in range(counter, 16):
                str_component.append('.')

            print(*str_component, sep='', end='\n')

            address = address + 16
            offset = offset + 16
            data_len = data_len - 16
        print('')

    @staticmethod
    def print_serial_ports() -> None:
        port_list = comports()

        print('Available serial ports:')
        for port in port_list:
            print(f'\t{port.device} - {port.description}')

    @staticmethod
    def open_terminal(ser: serial.Serial) -> None:
        """Attach an interactive terminal to the port

        Args:
            ser (serial.Serial): Serial port connected to the board
        """ 

        terminal = Miniterm(ser)
        terminal.set_rx_encoding('ascii')
        terminal.set_tx_encoding('ascii')
        terminal.start()
        terminal.join()

