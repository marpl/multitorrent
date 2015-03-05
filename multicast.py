from socket import *
import struct


def address_family(addr):
    """Guesses the family of an address (by looking for ':' in it)."""
    return ':' in addr and AF_INET6 or AF_INET


class MulticastSocket(socket):

    def __init__(self, family_or_addr, type=SOCK_DGRAM, ttl=1, loop=1):
        """
        family_or_addr should be either AF_INET, AF_INET6 or
        a tuple (ip_addr, port). In the latter case:
        - the family is guessed from the address
        - the socket is bound and the multicast group is joined
        Example tuple: ('ff01::114', 51234)
        """

        # Get the family
        if isinstance(family_or_addr, tuple):
            addr = family_or_addr
            family = address_family(addr[0])
        else:
            addr = None
            family = family_or_addr

        # Initialize the socket
        socket.__init__(self, family, type)

        # Set some useful properties
        if family == AF_INET:
            self.v6 = False
        elif family == AF_INET6:
            self.v6 = True
        else:
            raise ValueError('unknown socket family')
        self.ip_proto = self.v6 and IPPROTO_IPV6 or IPPROTO_IP
        self.ip_opt_prefix = self.v6 and 'IPV6_' or 'IP_'

        # Set some multicast options
        self.set_ip_opt(['MULTICAST_TTL', 'MULTICAST_HOPS'], ttl)
        self.set_ip_opt('MULTICAST_LOOP', loop)

        # Join the multicast if an addr was given
        if addr:
            self._join_group(*addr)

    def _join_group(self, addr, port):

        # Keep it simple, only one multicast per socket
        if hasattr(self, '_mreq'):
            raise RuntimeError('socket is already bound to a group')

        # Allow multiple sockets to listen to the same multicast
        self.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        try:
            self.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
        except NameError:
            pass  # Some systems don't support SO_REUSEPORT

        # Bind to port and inform the kernel that we want to join the multicast
        self.bind(('', port))
        mreq = inet_pton(self.family, addr) \
             + (b'\0'*4, b'')[self.v6]      \
             + struct.pack('i', 0)
        self.set_ip_opt(['ADD_MEMBERSHIP', 'JOIN_GROUP'], mreq)

        # Save the multicast addr, we'll need it to leave the multicast
        self._mreq = mreq

    def _leave_group(self):
        mreq = getattr(self, '_mreq', None)
        if mreq is not None:
            self.set_ip_opt(['DROP_MEMBERSHIP', 'LEAVE_GROUP'], mreq)

    def set_ip_opt(self, opt, value):
        """
        A wrapper for setsockopt() that makes it easier to support both IPv4
        and IPv6.

        The opt argument can be:
        - the name of an option without the IP prefix, e.g. 'MULTICAST_LOOP',
          which is mapped to either IP_MULTICAST_LOOP or IPV6_MULTICAST_LOOP
          depending on the socket's family
        - a list or tuple of 2 strings, e.g. ['ADD_MEMBERSHIP', 'JOIN_GROUP'],
          where the first is the name of the IPv4 option, and the second its
          IPv6 equivalent
        """
        if isinstance(opt, str):
            o = globals()[self.ip_opt_prefix+opt]
        elif isinstance(opt, list) or isinstance(opt, tuple):
            o = globals()[self.ip_opt_prefix+opt[self.v6]]
        else:
            raise TypeError('opt argument is of wrong type: '+repr(opt))
        self.setsockopt(self.ip_proto, o, value)

    def __del__(self):
        self._leave_group()
        self.close()
