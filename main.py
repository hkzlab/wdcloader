"""Main module"""

import argparse
from typing import Tuple, List

import serial

from src.loader_utilities import LoaderUtilities
from src.board_utilities import BoardUtilities, BoardCommands
from src.board_types import Board_Type

_PROG_NAME: str = 'wdcloader'
_PROG_VERSION: Tuple[int, int] = (0, 0)

def _build_argsparser() -> argparse.ArgumentParser:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog=_PROG_NAME,
        description='A tool for uploading and executing programs on an SXB or MMC board.'
    )
    
   
    parser.add_argument('--version', action='version', version=f'%(prog)s {_PROG_VERSION[0]}.{_PROG_VERSION[1]}')

    arg_group = parser.add_argument_group()
    arg_group.add_argument('-p', '--port',
                        required=True,
                        type=str,
                        nargs='?',
                        metavar="<serial port>",
                        help='Serial port associated with the board')
    
    mut_group = arg_group.add_mutually_exclusive_group()
    mut_group.add_argument('--load',
                        help='Load an <S19/S28 file>',
                        nargs=1,
                        type=str,
                        metavar='<S19/S28 file>',
                        required=False)
    mut_group.add_argument('--show',
                        help='Show memory at <hex_address> for <length> bytes',
                        nargs=2,
                        type=str,
                        metavar=('<hex_address>', '<length>'),
                        required=False)
    mut_group.add_argument('--save',
                        help='Save memory at <hex_address> for <length> bytes in <S28 file>',
                        nargs=3,
                        type=str,
                        metavar=('<hex_address>', '<length>', '<S28 file>'),
                        required=False)
    mut_group.add_argument('--savebin',
                        help='Save memory at <hex_address> for <length> bytes in <WDC file>',
                        nargs=3,
                        type=str,
                        metavar=('<hex_address>', '<length>', '<WDC file>'),
                        required=False)
    mut_group.add_argument('--loadbin',
                        help='Load from <WDC file>',
                        nargs=1,
                        type=str,
                        metavar='<WDC file>',
                        required=False)
    mut_group.add_argument('--loadraw',
                        help='Load from <raw file> and store at <hex_address>',
                        nargs=2,
                        type=str,
                        metavar=('<hex_address>', '<raw file>'),
                        required=False)
    mut_group.add_argument('--exec',
                        help='Exec code at <hex_address>',
                        nargs='+',
                        type=str,
                        metavar=('<hex_address>', '[open_terminal]'),
                        required=False)
    mut_group.add_argument('--term',
                        help='Exec terminal',
                        action='store_true',                 
                        required=False)

    return parser

if __name__ == '__main__':
    args = _build_argsparser().parse_args()

    if not args.port:
        LoaderUtilities.print_serial_ports()
    else:
        ser_port: serial.Serial = None

        try:
            ser_port = serial.Serial(port = args.port,
                                     bytesize = 8,
                                     stopbits = 1,
                                     parity = 'N',
                                     rtscts = True,
                                     timeout = 1.0)
            
            print('Resetting the board...')
            BoardUtilities.reset_board(ser_port)

            print('Reading the info block...')
            info_data = BoardCommands.read_info_data(ser_port)
            board_type = BoardUtilities.detect_board(info_data)

            print(f'Board type: {board_type.name}.')

            if board_type == Board_Type.UNKNOWN:
                raise RuntimeError('Unknown board detected!')

            if args.load:
                params = args.load
                print(f'Loading SREC file {params[0]} ...')
                LoaderUtilities.load_records(ser_port, params[0])
            elif args.loadbin:
                params = args.loadbin
                print(f'Loading WDC file {params[0]} ...')
                LoaderUtilities.load_binary(ser_port, params[0])
            elif args.loadraw:
                params = args.loadraw
                address = int(params[0], 16)
                filename = params[1]
                print(f'Loading raw file {filename} at address {'0x%.6X' % address} ...')
                LoaderUtilities.load_raw_binary(ser_port, address, filename)
            elif args.show:
                params = args.show
                address = int(params[0], 16)
                data_len = int(params[1])
                print(f'Showing {data_len} bytes at address {'0x%.6X' % address} ...')
                data = BoardCommands.read_memory(ser_port, address, data_len)
                LoaderUtilities.print_memory(address, data)
            elif args.save:
                params = args.save
                address = int(params[0], 16)
                data_len = int(params[1])
                filename = params[2]
                print(f'Saving {data_len} bytes from address {'0x%.6X' % address} in SREC file {filename} ...')
                data = BoardCommands.read_memory(ser_port, address, data_len)
                LoaderUtilities.save_records(address, data, filename)
            elif args.savebin:
                params = args.savebin
                address = int(params[0], 16)
                data_len = int(params[1])
                filename = params[2]
                print(f'Saving {data_len} bytes from address {'0x%.6X' % address} in BINARY file {filename} ...')
                data = BoardCommands.read_memory(ser_port, address, data_len)
                LoaderUtilities.save_binary(address, data, filename)
            elif args.exec:
                params = args.exec
                address = int(params[0], 16)
                print(f'Executing at address {'0x%.6X' % address} ...')
                BoardCommands.execute_memory(ser_port, address, board_type)

                if len(params) > 1 and params[1]:
                    print('Opening a serial terminal ...')
                    LoaderUtilities.open_terminal(ser_port)

            elif args.term:
                print('Opening a serial terminal ...')
                LoaderUtilities.open_terminal(ser_port)

        finally:
            if ser_port and not ser_port.closed:
                ser_port.close()

        print('Bye bye!')

