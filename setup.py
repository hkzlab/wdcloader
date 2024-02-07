import wdcloader
from setuptools import setup, find_packages

with open("doc/PyPI.md", "r") as fh:
    long_description = fh.read()

setup(
    name = 'wdcloader',
    version = f'{wdcloader._PROG_VERSION[0], wdcloader._PROG_VERSION[1]}',
    packages = find_packages(exclude=["doc", "tests"]),
    install_requires = ["pyserial>=3.5"],
    extras_require = {
    },
    entry_points = {
        "console_scripts": [
            "stcgal = wdcloader:cli",
        ],
    },
    description = "Loader utility for WDC 65xxx boards",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    keywords = "mcu microcontroller 6502 65816 wdc",
    url = "https://github.com/hkzlab/wdcloader",
    author = "Fabio Battaglia",
    license = "MIT License",
    platforms = "any",
    classifiers = [
    ],
    test_suite = "tests",
)