"""Parsers."""


import re
from collections import defaultdict
from enum import Enum
from typing import Any, Callable, Dict, Generator, cast
import datetime
import time
import logging

log = logging.getLogger(__name__)

TELEGRAM_TEMPLATE = '{txrx},{id},{command}'

DELIM = ','
PACKET_RECEIVED = 'REC|OK|ID|GETP|RDP'

packet_header_re = re.compile(PACKET_RECEIVED)


class PacketHeader(Enum):
    """Packet source identification."""

    send = 'TXP'
    status_ok = 'OK'
    status_error = 'ERROR'
    receive = 'REC'
    identify = 'ID'
    positions = 'GETP'
    position = 'RDP'


#def valid_packet(packet: str) -> bool:
def valid_packet(packet: str):
    """Verify if packet is valid.

    >>> # Check invalid packet due to leftovers in serial buffer
    """
    return bool(packet_header_re.match(packet))


def decode_packet(packet: str) -> dict:
    """Break packet down into primitives, and do basic interpretation.

    """
    packet = packet.replace('\r','')
    telegram = packet.split(DELIM)

    data = cast(Dict[str, Any], {
        'header': PacketHeader(telegram[0]).name,
    })

    # ack response
    if telegram[0] == 'ERROR':
        data['ok'] = False

    elif telegram[0] == 'OK':
        data['ok'] = True

    # external command received
    elif telegram[0] == 'REC':
        data['id'] = telegram[1]
        data['command'] = telegram[2]

    # its a regular packet
    else:
        data = telegram

    return data


def encode_packet(packet: dict) -> str:
    """Construct packet string from packet dictionary.

    """
    return TELEGRAM_TEMPLATE.format(
        txrx=PacketHeader.send.value,
        **packet
    )
