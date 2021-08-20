"""Command line interface for easywave library.

Usage:
  easywave [-v | -vv] [options]
  easywave [-v | -vv] [options] <command> <id>
  easywave (-h | --help)
  easywave --version

Options:
  -p --port=<port>         Serial port to connect to,
                             or TCP port in TCP mode.
  --baud=<baud>            Serial baud rate [default: 57600].
  --host=<host>            TCP mode, connect to host instead of serial port.
  -h --help                Show this screen.
  -v                       Increase verbosity
  --version                Show version.
"""

import asyncio
import logging
import sys
from typing import Dict, Optional, Sequence, Type  # noqa: unused-import

import pkg_resources
from docopt import docopt

from .protocol import EasywaveProtocol, create_easywave_connection


def main(
    argv: Sequence[str] = sys.argv[1:], loop: Optional[asyncio.AbstractEventLoop] = None
) -> None:
    """Parse argument and setup main program loop."""
    args = docopt(
        __doc__, argv=argv, version=pkg_resources.require("easywave")[0].version
    )

    level = logging.ERROR
    if args["-v"]:
        level = logging.INFO
    if args["-v"] == 2:
        level = logging.DEBUG
    logging.basicConfig(level=level)

    if not loop:
        loop = asyncio.get_event_loop()

    conn = create_easywave_connection(
        protocol=EasywaveProtocol,
        host=args["--host"],
        port=args["--port"],
        baud=args["--baud"],
        loop=loop,
    )

    transport, protocol = loop.run_until_complete(conn)

    try:
        if args["<command>"]:
            loop.run_until_complete(protocol.send_command_ack(args["<id>"], args["<command>"]))
        else:
            loop.run_forever()
    except KeyboardInterrupt:
        # cleanup connection
        transport.close()
        loop.run_forever()
    finally:
        loop.close()


if __name__ == "__main__":
    # execute only if run as a script
    main()
