# -*- coding: utf-8 -*-

from __future__ import division

from Queue import Empty, Queue
import random
from time import sleep
import struct
from threading import Thread, current_thread

from libtorrent import *

from alerts import Alerts
from multicast import MulticastSocket, address_family, timeout
from piece import Piece



## Alert classes

class multicast_alert(str):
    """Base class for multicast alerts."""
    prefix = 'multicast: '
    __new__ = lambda cls, s='': str.__new__(cls, cls.prefix+s)

class multicast_invalid_alert(multicast_alert):
    """Emitted when an invalid message is received."""
    prefix = 'multicast: received invalid message: '

class multicast_duplicate_alert(multicast_alert):
    """Emitted when a block is received that we already had."""
    prefix = 'multicast: received a block we already have'



## Order functions

def random_order(pieces, previous):
    return random.choice(list(pieces))

def first_to_last_order(pieces, previous):
    piece_num = previous
    while True:
        piece_num = (piece_num + 1) % len(pieces)
        if piece_num in pieces:
            break
    return piece_num



## Session class

class Session(Alerts, session):

    def dispatch_alerts(self, timeout=1000):
        self.wait_for_alert(timeout)
        for alert in self.pop_alerts():
            self.emit(alert)

    def multicast_recv(self, *args):
        t = Thread(target=self.multicast_recv_loop, args=args)
        t.daemon = True
        t.start()
        return t

    def multicast_recv_loop(self, torrent, addr):
        s = MulticastSocket(addr)
        s.settimeout(2)
        incoming = {}
        while True:
            if getattr(current_thread(), 'stop', False):
                break
            try:
                msg = s.recv(16500)
            except timeout:
                continue
            if len(msg) < 14:
                self.emit(multicast_invalid_alert('too short: %i' % len(msg)))
                continue
            length = struct.unpack('!i', msg[:4])[0] - 9
            msg_type = struct.unpack('!B', msg[4])[0]
            piece_num = struct.unpack('!i', msg[5:9])[0]
            offset = struct.unpack('!i', msg[9:13])[0]
            if msg_type != 7:
                self.emit(multicast_invalid_alert('unknown type: %i' % msg_type))
                continue
            if torrent.have_piece(piece_num):
                incoming.pop(piece_num, None)
                self.emit(multicast_duplicate_alert())
                continue
            data = msg[13:]
            if len(data) != length:
                e = 'lengths do not match: %i ≠ %i' % (len(data), length)
                self.emit(multicast_invalid_alert(e))
                continue
            m = 'received block (%i, %i) of piece %i on %s' % (offset, length, piece_num, addr)
            self.emit(multicast_alert(m))
            if piece_num not in incoming:
                incoming[piece_num] = Piece(torrent, piece_num)
            piece = incoming[piece_num]
            piece.add_block(offset, length, data)
            if piece.progress.is_complete:
                torrent.add_piece(piece_num, bytes(piece.buf), 0)
                incoming.pop(piece_num)

    def multicast_send(self, *args, **kwargs):
        t = Thread(target=self.multicast_send_loop, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()
        return t

    def multicast_send_loop(self, torrent, addr, block_size=16384,
                            blocks_per_second=2, order=random_order):
        q = Queue()
        waiting_for = set()
        def queue_piece(alert):
            if alert.piece in waiting_for:
                q.put(alert)
        self.on(read_piece_alert, queue_piece)
        sleep_time = 1 / blocks_per_second
        sock = MulticastSocket(address_family(addr[0]))
        last_asked_piece_num = -1
        while True:
            if getattr(current_thread(), 'stop', False):
                break

            # Get the set of available pieces
            status = torrent.status(24)
            pieces = enumerate(status.verified_pieces or status.pieces)
            pieces = set([i for i, b in pieces if b])
            if not pieces:
                # No pieces have been completed yet, wait and try again
                sleep(10)
                continue

            # Send read requests to libtorrent for up to 3 pieces
            while len(waiting_for) < min(3, len(pieces)):
                last_asked_piece_num = order(pieces, last_asked_piece_num)
                waiting_for.add(last_asked_piece_num)
                torrent.read_piece(last_asked_piece_num)

            # Wait for the result, should be instantaneous after the first piece
            try:
                alert = q.get(True, 1)
            except Empty:
                # Timeout, start over
                waiting_for = set()
                last_asked_piece_num = -1
                continue

            # Check the result
            piece_num = alert.piece
            waiting_for.remove(piece_num)
            piece = alert.buffer
            if not piece:
                e = 'failed to read piece %i: %s' % (piece_num, alert)
                self.emit(multicast_alert(e))
                continue

            # Send the piece in blocks
            for offset in range(0, len(piece), block_size):
                length = min(len(piece) - offset, block_size)
                msg = struct.pack('!i', 9 + length) \
                    + struct.pack('!B', 7)          \
                    + struct.pack('!i', piece_num)  \
                    + struct.pack('!i', offset)     \
                    + piece[offset:offset+length]
                sock.sendto(msg, addr)
                m = 'sent block (%i, %i) of piece %i to %s' % (offset, length, piece_num, addr)
                self.emit(multicast_alert(m))
                sleep(sleep_time)
