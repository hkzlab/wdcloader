"""This module contains an enum for all supported board types"""

from enum import Enum

class Board_Type(Enum):
    W65C02SXB = 0
    W65C816SXB = 1
    W65C165SXB_A = 2
    W65C165SXB_B = 3
    W65C165SXB_C = 4
    UNKNOWN = 100

