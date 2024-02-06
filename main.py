"""Main module"""

import argparse
import logging
from typing import Tuple, List

import serial

from src.loader_utilities import LoaderUtilities

_PROG_NAME: str = 'wdcloader'
_PROG_VERSION: Tuple[int, int] = (0, 0)

_LOGGER: logging.Logger

def _build_argsparser() -> argparse.ArgumentParser:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog=_PROG_NAME,
        description='A tool for uploading and executing programs on an SXB or MMC board.'
    )
    
   
    parser.add_argument('--version', action='version', version=f'%(prog)s {_PROG_VERSION[0]}.{_PROG_VERSION[1]}')

    arg_group = parser.add_argument_group()
    arg_group.add_argument('-v', '--verbose', action='count', default=0)
    arg_group.add_argument('-p', '--port',
                        required=True,
                        type=str,
                        metavar="<serial port>",
                        help='Serial port associated with the board')
    mut_group = arg_group.add_mutually_exclusive_group(required=True) # Require at least one parameter from these

    mut_group.add_argument('--tload',
                        help='Load an <S19/S28 file>',
                        nargs=1,
                        type=str,
                        metavar='<S19/S28 file>',
                        required=False)
    mut_group.add_argument('--tshow',
                        help='Show memory at <address> for <length> bytes',
                        nargs=2,
                        type=str,
                        metavar=('<address>', '<length>'),
                        required=False)
    mut_group.add_argument('--tsave',
                        help='Save memory at <address> for <length> bytes in <S28 file>',
                        nargs=3,
                        type=str,
                        metavar=('<address>', '<length>', '<S28 file>'),
                        required=False)
    mut_group.add_argument('--tloadbin',
                        help='Load from <WDC file>',
                        nargs=1,
                        type=str,
                        metavar='<WDC file>',
                        required=False)
    mut_group.add_argument('--exec',
                        help='Exec code at <address>',
                        nargs=1,
                        type=str,
                        metavar='<address>',
                        required=False)
    mut_group.add_argument('--tterm',
                        help='Exec terminal',
                        action='store_true',                 
                        required=False)

    return parser

if __name__ == '__main__':
    args = _build_argsparser().parse_args()

    print(f'{args}')

    ser_port: serial.Serial = None

    try:
        ser_port = serial.Serial(port = args.port,
                                 bytesize = 8,
                                 stopbits = 1,
                                 parity = 'N',
                                 rtscts = True,
                                 timeout = 1.0)
    finally:
        if ser_port and not ser_port.closed:
            ser_port.close();
        print('Bye bye!')

