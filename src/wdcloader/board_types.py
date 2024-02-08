"""This module contains an enum for all supported board types"""

from enum import Enum

class Board_Type(Enum):
    W65C02SXB = 0
    W65C816SXB = 1
    MyMENSCH_RevA = 2
    MyMENSCH_RevB = 3
    MyMENSCH_RevC = 4
    UNKNOWN = 100

