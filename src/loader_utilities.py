"""This module contains utility code for the loader"""

from typing import final

import serial

from board_utilities import BoardCommands

@final
class LoaderUtilities:
    """
    This class contains higher level utilities for the loader, to support
    various types of inbound and outboud data.
    """

    def load_records(ser: serial.Serial, filename: str) -> None:
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