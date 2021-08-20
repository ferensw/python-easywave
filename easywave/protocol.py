"""Asyncio protocol implementation of Eldat Easywave."""

import asyncio
import concurrent
import logging
import time
from datetime import timedelta
from functools import partial
from typing import Callable, List

from serial_asyncio import create_serial_connection
from serial.tools import list_ports

from .parser import (
    decode_packet,
    encode_packet,
    valid_packet
)

log = logging.getLogger(__name__)
easywave_log = None

TIMEOUT = timedelta(seconds=5)


class ProtocolBase(asyncio.Protocol):
    """Manage low level easywave protocol."""

    transport = None  # type: asyncio.Transport

    def __init__(self, loop=None, disconnect_callback=None) -> None:
        """Initialize class."""
        if loop:
            self.loop = loop
        else:
            self.loop = asyncio.get_event_loop()
        self.packet = ''
        self.buffer = ''
        self.packet_callback = None
        self.disconnect_callback = disconnect_callback
        self.old_time = time.time()
        self.old_data = ''

    def connection_made(self, transport):
        """Just logging for now."""
        self.transport = transport
        log.debug('connected')

    def data_received(self, data):
        """Add incoming data to buffer."""
        log.debug('received bytes: %s', data)
        """Ignore repetitive commands from remote"""
        rec_time = time.time()
        rec_data = data
        if rec_data != self.old_data or rec_time - self.old_time > 1 or data == b'OK\r':
            try:
                data = data.decode()
            except UnicodeDecodeError:
                invalid_data = data.decode(errors="replace")
                log.warning("Error during decode of data, invalid data: %s", invalid_data)
            else:
                self.buffer = data.strip()
                self.old_time = rec_time
                self.old_data = rec_data
                self.handle_data()

    def handle_data(self):
        """Check incoming data if valid."""
        log.debug('received buffer: %s', self.buffer)
        if valid_packet(self.buffer):
            self.handle_raw_packet(self.buffer)
        else:
            log.warning('dropping invalid data: %s', self.buffer)

    def handle_raw_packet(self, raw_packet: bytes) -> None:
        """Handle one raw incoming packet."""
        raise NotImplementedError()

    def send_raw_packet(self, packet: str):
        """Encode and put packet string onto write buffer."""
        data = packet + '\r\n'
        log.debug('writing data: %s', repr(data))
        self.transport.write(data.encode())

    def log_all(self, file):
        """Log all data received from Easywave to file."""
        global easywave_log
        if file == None:
            easywave_log = None
        else:
            log.debug('logging to: %s', file)
            easywave_log = open(file, 'a')

    def connection_lost(self, exc):
        """Log when connection is closed, if needed call callback."""
        if exc:
            log.exception('disconnected due to exception')
        else:
            log.info('disconnected because of close/abort.')
        if self.disconnect_callback:
            self.disconnect_callback(exc)


class EasywaveProtocol(ProtocolBase):
    """Handle translating easywave packets to/from python primitives."""

    def __init__(self, *args, packet_callback = None,
                 **kwargs) -> None:
        """Add packethandling specific initialization.

        packet_callback: called with every complete/valid packet
        received.
        """
        super().__init__(*args, **kwargs)
        if packet_callback:
            self.packet_callback = packet_callback
        self._command_ack = asyncio.Event(loop=self.loop)
        self._ready_to_send = asyncio.Lock(loop=self.loop)

    def handle_raw_packet(self, raw_packet):
        """Parse raw packet string into packet dict."""
        log.debug('got packet: %s', raw_packet)
        if easywave_log:
            print(raw_packet, file=easywave_log)
            easywave_log.flush()
        packet = None
        try:
            packet = decode_packet(raw_packet)
        except:
            log.exception('failed to parse packet: %s', packet)

        log.debug('decoded packet: %s', packet)

        if packet:
            if 'ok' in packet:
                # handle response packets internally
                log.debug('command response: %s', packet)
                self._last_ack = packet
                self._command_ack.set()
            else:
                self.handle_packet(packet)
        else:
            log.warning('no valid packet')

    def handle_packet(self, packet):
        """Process incoming packet dict and optionally call callback."""
        if self.packet_callback:
            # forward to callback
            self.packet_callback(packet)
        else:
            print('packet', packet)

    def send_packet(self, fields):
        """Concat fields and send packet to rx09."""
        self.send_raw_packet(encode_packet(fields))

    def send_command(self, device_id, action):
        """Send device command to easywave rx09."""
        command = {}
        command['id'] = device_id
        command['command'] = action
        log.debug('sending command: %s', command)
        self.send_packet(command)

#    @asyncio.coroutine
    async def send_command_ack(self, device_id, action):
        """Send command, wait for rx09 to repond with acknowledgment."""
        await self._ready_to_send.acquire()
        acknowledgement = None
        try:
            self._command_ack.clear()
            self.send_command(device_id, action)
            log.debug('waiting for acknowledgement')
            try:
                await asyncio.wait_for(self._command_ack.wait(),
                                            TIMEOUT.seconds, loop=self.loop)
                log.debug('packet acknowledged')
            except concurrent.futures._base.TimeoutError:
                acknowledgement = {'ok': False, 'message': 'timeout'}
                log.warning('acknowledge timeout')
            else:
                acknowledgement = self._last_ack.get('ok', False)
        finally:
            # allow next command
            self._ready_to_send.release()
        return acknowledgement


def create_easywave_connection(port=None, host=None, baud=57600, protocol=EasywaveProtocol,
                             packet_callback=None, disconnect_callback=None, loop=None):
    """Create Easywave manager class, returns transport coroutine."""
    # use default protocol if not specified
    protocol = partial(
        protocol,
        loop=loop if loop else asyncio.get_event_loop(),
        packet_callback=packet_callback,
        disconnect_callback=disconnect_callback,
    )

    if not port:
        usb_port = list(list_ports.grep("Easywave"))[0]
        port = usb_port.device
        log.debug('USB port: %s', port)

    # setup serial connection if no transport specified
    if host:
        conn = loop.create_connection(protocol, host, port)
    else:
        baud = baud
        conn = create_serial_connection(loop, protocol, port, baud)

    return conn
