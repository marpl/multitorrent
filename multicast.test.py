import socket
import unittest

from multicast import MulticastSocket, AF_INET, AF_INET6


msg = b'ping'


class TestMulticastSocket(unittest.TestCase):

    def test_IPv4(self):
        addr = ('224.0.0.254', 50000)
        r1 = MulticastSocket(addr)
        r2 = MulticastSocket(addr)
        s = MulticastSocket(AF_INET)
        self.assertEqual(s.sendto(msg, addr), len(msg))
        self.assertEqual(r1.recv(1024), msg)
        self.assertEqual(r2.recv(1024), msg)

    def test_IPv6(self):
        addr = ('ff01::114', 50000)
        r1 = MulticastSocket(addr)
        r2 = MulticastSocket(addr)
        s = MulticastSocket(AF_INET6)
        self.assertEqual(s.sendto(msg, addr), len(msg))
        self.assertEqual(r1.recv(1024), msg)
        self.assertEqual(r2.recv(1024), msg)


if __name__ == '__main__':
    unittest.main()
