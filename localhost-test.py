#!/usr/bin/env python2

from __future__ import print_function

import argparse
import socket
from time import sleep

import libtorrent_plus as lt


def main():
    p = argparse.ArgumentParser()
    p.add_argument('torrent_file', type=argparse.FileType('rb'))
    p.add_argument('-4', dest='force_v4', action='store_true')
    p.add_argument('-a', '--addr', default=None)
    p.add_argument('-p', '--port', type=int, default=50000)
    cmd_args = p.parse_args()

    a = cmd_args.addr
    if not a:
        if socket.has_ipv6 and not cmd_args.force_v4:
            a = 'ff01::114'
        else:
            a = '224.0.0.254'
    addr = (a, cmd_args.port)

    e = lt.bdecode(cmd_args.torrent_file.read())
    torrent_info = lt.torrent_info(e)

    print('Torrent name is: ', torrent_info.name())
    print('InfoHash is: ', torrent_info.info_hash())
    print('Number of pieces: ', torrent_info.num_pieces())

    send_ses = lt.Session(flags=0)
    send_ses.on(lt.multicast_alert, print)
    send_torrent = send_ses.add_torrent(torrent_info, 'torrents/complete')
    print('checking data...')
    while 'checking' in str(send_torrent.status(0).state):
        sleep(.1)
    if not send_torrent.status(0).is_finished:
        print('failure, some files of the torrent are missing or corrupted.')
        print('you need a full copy in the torrents/complete directory for this test to work')
        exit(1)
    send_ses.pause()
    send_thread1 = send_ses.multicast_send(send_torrent, addr, order=lt.random_order)
    send_thread2 = send_ses.multicast_send(send_torrent, addr, order=lt.first_to_last_order)

    recv_ses = lt.Session()
    recv_ses.set_alert_mask(129)
    recv_ses.on(lt.block_finished_alert, print)
    recv_ses.on(lt.piece_finished_alert, print)
    recv_ses.on(lt.multicast_alert, print)
    recv_ses.start_dht()
    recv_torrent = recv_ses.add_torrent(torrent_info, 'torrents/downloading')
    recv_thread = recv_ses.multicast_recv(recv_torrent, addr)

    try:
        while True:
            recv_ses.dispatch_alerts(500)
            send_ses.dispatch_alerts(500)
    except (KeyboardInterrupt, EOFError):
        print('\nExiting...')
        recv_thread.stop = True
        send_thread1.stop = True
        send_thread2.stop = True
        exit(0)


if __name__ == '__main__':
    main()
