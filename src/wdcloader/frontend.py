"""Frontend module"""

import argparse
import traceback

import serial

from wdcloader import __name__, __version__
from wdcloader.loader_utilities import LoaderUtilities
from wdcloader.board_utilities import BoardUtilities, BoardCommands
from wdcloader.board_types import Board_Type

def _build_argsparser() -> argparse.ArgumentParser:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog=__name__,
        description='A tool for uploading and executing programs on an SXB or MMC board.'
    )
    
   
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('-v', '--verbose', action='count', default=0)

    arg_group = parser.add_argument_group()
    arg_group.add_argument('-p', '--port',
                        required=True,
                        type=str,
                        nargs='?',
                        metavar="<serial port>",
                        help='Serial port associated with the board')
    
    arg_group.add_argument('--show',
                        help='Show memory at <hex_address> for <length> bytes',
                        nargs=2,
                        type=str,
                        metavar=('<hex_address>', '<length>'),
                        required=False)

    arg_group.add_argument('--exec',
                        help='Exec code at <hex_address>',
                        nargs=1,
                        type=str,
                        metavar='<hex_address>',
                        required=False)

    arg_group.add_argument('--term',
                        help='Exec terminal after the other commands have executed',
                        action='store_true',                 
                        required=False)
    
    mut_group = arg_group.add_mutually_exclusive_group()
    mut_group.add_argument('--load',
                        help='Load an <S19/S28 file>',
                        nargs=1,
                        type=str,
                        metavar='<S19/S28 file>',
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

    return parser

def cli() -> int:
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

            if args.show:
                params = args.show
                address = int(params[0], 16)
                data_len = int(params[1])
                print(f'Showing {data_len} bytes at address {'0x%.6X' % address} ...')
                data = BoardCommands.read_memory(ser_port, address, data_len)
                LoaderUtilities.print_memory(address, data)

            if args.exec:
                params = args.exec
                address = int(params[0], 16)
                print(f'Executing at address {'0x%.6X' % address} ...')
                BoardCommands.execute_memory(ser_port, address, board_type)

                if len(params) > 1 and params[1]:
                    print('Opening a serial terminal ...')
                    LoaderUtilities.open_terminal(ser_port)

            if args.term:
                print('Opening a serial terminal ...')
                LoaderUtilities.open_terminal(ser_port)

        except Exception as ex:
            if args.verbose:
                print(traceback.format_exc())
            else:
                print(ex)
            return -1

        finally:
            if ser_port and not ser_port.closed:
                ser_port.close()

        print('Bye bye!')
        return 1 