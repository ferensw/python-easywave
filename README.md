Python Easywave library
=====================

Library and CLI tool for interacting with Eldat RX09 Easywave transceiver.

Requirements
------------

- Python 2.7 or 3.6 (or higher)

Description
-----------

This package is a library for interacting with an Eldat RX09 Easywave transceiver. See https://www.eldat.de/produkte/schnittstellen/rx09e_en.html
I created this to be able to control my window screens.
Specification of how to use the transceiver: https://www.eldat.de/produkte/_div/rx09e_sp_en.pdf
I don't know if this also works Niko Easywave, so be my guest to test it...

Installation
------------

    $ pip install easywave

Usage of Easywave CLI
-------------------------

    $ easywave -h
    Command line interface for easywave library.

    Usage:
      easywave [-v | -vv] [options]
      easywave [-v | -vv] [options] <command> <id>
      easywave (-h | --help)
      easywave --version

    Options:
      -p --port=<port>   Serial port to connect to [default: auto detect],
                           or TCP port in TCP mode.
      --baud=<baud>      Serial baud rate [default: 57600].
      --host=<host>      TCP mode, connect to host instead of serial port.
      -m=<handling>      How to handle incoming packets [default: event].
      -h --help          Show this screen.
      -v                 Increase verbosity
      --version          Show version.

Command can be code "A", "B", "C" or "D". ID is channel id.

Intercept and display Easywave packets:

    $ easywave
    packet {'header': 'receive', 'id': '1c14a3', 'command': 'A'}

Send a command:

    $ easywave A 01

