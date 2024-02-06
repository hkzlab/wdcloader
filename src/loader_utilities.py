"""This module contains utility code for the loader"""

from typing import final
import struct

import serial

from board_utilities import BoardCommands

@final
class LoaderUtilities:
    """
    This class contains higher level utilities for the loader, to support
    various types of inbound and outboud data.
    """

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
                    data = bytearray.fromhex(line[8:(count*2)+8])
                    # Ignore the checksum for now
                    BoardCommands.write_memory(ser, address, data)
                elif line.startswith('S2'): # 24 bit address record
                    count = int(line[2:4], 16) - 4
                    address = int(line[4:10], 16)
                    data = bytearray.fromhex(line[10:(count*2)+10])
                    # Ignore the checksum for now
                    BoardCommands.write_memory(ser, address, data)

                total = total + count
        finally:
            file.close()

        print(f'Loaded {total} bytes from {filename}.')

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

                BoardCommands.write_memory(ser, address, data)

                total = total + size
        finally:
            file.close()

        print(f'Loaded {total} bytes from {filename}.')

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

