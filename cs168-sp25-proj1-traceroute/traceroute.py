import util

# Your program should send TTLs in the range [1, TRACEROUTE_MAX_TTL] inclusive.
# Technically IPv4 supports TTLs up to 255, but in practice this is excessive.
# Most traceroute implementations cap at approximately 30.  The unit tests
# assume you don't change this number.
TRACEROUTE_MAX_TTL = 30

# Cisco seems to have standardized on UDP ports [33434, 33464] for traceroute.
# While not a formal standard, it appears that some routers on the internet
# will only respond with time exceeeded ICMP messages to UDP packets send to
# those ports.  Ultimately, you can choose whatever port you like, but that
# range seems to give more interesting results.
TRACEROUTE_PORT_NUMBER = 33434  # Cisco traceroute port number.

# Sometimes packets on the internet get dropped.  PROBE_ATTEMPT_COUNT is the
# maximum number of times your traceroute function should attempt to probe a
# single router before giving up and moving on.
PROBE_ATTEMPT_COUNT = 3

class IPv4:
    # Each member below is a field from the IPv4 packet header.  They are
    # listed below in the order they appear in the packet.  All fields should
    # be stored in host byte order.
    #
    # You should only modify the __init__() method of this class.
    version: int
    header_len: int  # Note length in bytes, not the value in the packet.
    tos: int         # Also called DSCP and ECN bits (i.e. on wikipedia).
    length: int      # Total length of the packet.
    id: int
    flags: int
    frag_offset: int
    ttl: int
    proto: int
    cksum: int
    src: str
    dst: str

    def __init__(self, buffer: bytes):
        bits = ''.join(format(byte, '08b') for byte in [*buffer])
        self.version = int(bits[0:4], 2)
        self.header_len = int(bits[4:8], 2) * 4
        self.tos = int(bits[8:16], 2)
        self.length = int(bits[16:32], 2)
        self.id = int(bits[32:48], 2)
        self.flags = int(bits[48:51], 2)
        self.frag_offset = int(bits[51:64], 2)
        self.ttl = int(bits[64:72], 2)
        self.proto = int(bits[72:80], 2)
        self.cksum = int(bits[80:96], 2)
        byte_src = buffer[12:16]
        self.src = util.inet_ntoa(byte_src)
        self.dst = util.inet_ntoa(buffer[16:20])
        pass  # TODO

    def __str__(self) -> str:
        return f"IPv{self.version} (tos 0x{self.tos:x}, ttl {self.ttl}, " + \
            f"id {self.id}, flags 0x{self.flags:x}, " + \
            f"ofsset {self.frag_offset}, " + \
            f"proto {self.proto}, header_len {self.header_len}, " + \
            f"len {self.length}, cksum 0x{self.cksum:x}) " + \
            f"{self.src} > {self.dst}"


class ICMP:
    # Each member below is a field from the ICMP header.  They are listed below
    # in the order they appear in the packet.  All fields should be stored in
    # host byte order.
    #
    # You should only modify the __init__() function of this class.
    type: int
    code: int
    cksum: int

    def __init__(self, buffer: bytes):
        bits = ''.join(format(byte, '08b') for byte in [*buffer])
        self.type = int(bits[:8], 2)
        self.code = int(bits[8:16], 2)
        self.cksum = int(bits[16:32], 2) 
        pass  # TODO

    def __str__(self) -> str:
        return f"ICMP (type {self.type}, code {self.code}, " + \
            f"cksum 0x{self.cksum:x})"


class UDP:
    # Each member below is a field from the UDP header.  They are listed below
    # in the order they appear in the packet.  All fields should be stored in
    # host byte order.
    #
    # You should only modify the __init__() function of this class.
    src_port: int
    dst_port: int
    len: int
    cksum: int

    def __init__(self, buffer: bytes):
        bits = ''.join(format(byte, '08b') for byte in [*buffer])
        self.src_port = int(bits[:16], 2)
        self.dst_port = int(bits[16:32], 2)
        self.len = int(bits[32:48], 2)
        self.cksum = int(bits[48:], 2)
        pass  # TODO

    def __str__(self) -> str:
        return f"UDP (src_port {self.src_port}, dst_port {self.dst_port}, " + \
            f"len {self.len}, cksum 0x{self.cksum:x})"

# TODO feel free to add helper functions if you'd like
def slice_byte(buffer_byte: bytes):         # Slice bytes of buffer into three bytes (2*IPv4 ICMP UDP)
    route_IPv4 = IPv4(buffer_byte[:20])
    route_ICMP = ICMP(buffer_byte[route_IPv4.header_len: route_IPv4.header_len + 8])
    my_IPv4 = IPv4(buffer_byte[route_IPv4.header_len + 8: route_IPv4.header_len + 28])
    udp = UDP(buffer_byte[route_IPv4.header_len + 28: route_IPv4.header_len + 36])
    return (route_IPv4, route_ICMP, my_IPv4, udp)

def check_payload(my_ip: IPv4):  # Check UDP can be parsed
    return my_ip.version == 4 and my_ip.proto == util.IPPROTO_UDP

def traceroute(sendsock: util.Socket, recvsock: util.Socket, ip: str) \
        -> list[list[str]]:
    """ Run traceroute and returns the discovered path.

    Calls util.print_result() on the result of each TTL's probes to show
    progress.

    Arguments:
    sendsock -- This is a UDP socket you will use to send traceroute probes.
    recvsock -- This is the socket on which you will receive ICMP responses.
    ip -- This is the IP address of the end host you will be tracerouting.

    Returns:
    A list of lists representing the routers discovered for each ttl that was
    probed.  The ith list contains all of the routers found with TTL probe of
    i+1.   The routers discovered in the ith list can be in any order.  If no
    routers were found, the ith list can be empty.  If `ip` is discovered, it
    should be included as the final element in the list.
    """

    # TODO Add your implementation
    # for ttl in range(1, TRACEROUTE_MAX_TTL+1):
    #     util.print_result([], ttl)
    # return []
    msg = "miku"
    route_IPs = []
    for i in range(TRACEROUTE_MAX_TTL):     # TTL == i + 1
        sendsock.set_ttl(i + 1)
        IPs = []
        ids = []
        duplicate = False
        for attemp_times in range(PROBE_ATTEMPT_COUNT):
            sendsock.sendto(msg.encode(), (ip, TRACEROUTE_PORT_NUMBER))
        while True:
            if len(ids) == 3 and not duplicate:
                break

            if not recvsock.recv_select():
                break

            buff, address = recvsock.recvfrom()

            if len(buff) < 56: # test b6: check len of buff
                continue

            route_IP, route_ICMP, my_IP, udp = slice_byte(buff)

            if route_IP.proto != 1: # check b7
                continue

            if route_ICMP.type not in (3, 11):  # check b2
                continue

            if route_ICMP.type == 11 and route_ICMP.code != 0:  # check  b3
                continue

            if not check_payload(my_IP): # check b5
                continue

            if my_IP.ttl != i + 1:
                continue

            if my_IP.dst != ip:
                continue

            if udp.dst_port != TRACEROUTE_PORT_NUMBER:
                continue

            if my_IP.id in ids:
                duplicate = True
                continue
            else:
                ids.append(my_IP.id)

            if route_IP.src == ip:
                route_IPs.append([ip])
                return route_IPs
            elif route_IP.src not in IPs:
                IPs.append(route_IP.src)
            
        route_IPs.append(IPs)
    return route_IPs
if __name__ == '__main__':
    args = util.parse_args()
    ip_addr = util.gethostbyname(args.host)
    print(f"traceroute to {args.host} ({ip_addr})")
    route_IPs = traceroute(util.Socket.make_udp(), util.Socket.make_icmp(), ip_addr)
    for i in range(len(route_IPs)):
        ttl = i + 1
        util.print_result(route_IPs[i], ttl)