#!/usr/bin/python
"""
Generates a packet with a constant settings for a given payload
"""
import sys
from scapy.all import Ether, IP, TCP, Raw, wrpcap

PCAP_NAME = 'a.pcap'
SRC_MAC = "00:50:56:b3:c7:fb"
DST_MAC = "00:50:56:b3:c7:fc"
SRC_IP = "4.4.4.4"
DST_IP = "4.4.4.5"
RANDOM_PORT = 12345
TARGET_PORT = 1010

def build_pcap(payload, src_port, dst_port):
    """
    Building a pcap from the given payload and the ports
    """
    # Build all the layers
    ethernet_layer = Ether(dst=SRC_MAC, src=DST_MAC)
    ip_layer = IP(src=SRC_IP, dst=DST_IP)
    tcp_layer = TCP(sport=src_port, dport=dst_port)
    payload = Raw(load=bytearray.fromhex(payload))

    complete_packet = ethernet_layer/ip_layer/tcp_layer/payload

    wrpcap(PCAP_NAME, complete_packet)


def main():
    """
    Main function
    """
    if sys.argv[1] == '-r':
        build_pcap(sys.argv[2], TARGET_PORT, RANDOM_PORT)
    else:
        build_pcap(sys.argv[1], RANDOM_PORT, TARGET_PORT)

if __name__ == "__main__":
    main()
