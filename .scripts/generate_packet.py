"""
Generates a packet with a constant settings for a given payload
"""
from scapy.all import *

PCAP_NAME = 'a.pcap'
SRC_MAC = "00:50:56:b3:c7:fb"
DST_MAC = "00:50:56:b3:c7:fc"
SRC_IP = "4.4.4.4"
DST_IP = "4.4.4.5"
SRC_PORT = 12345
DST_PORT = 1010


def main():
    """
    Main function
    """
    # Build all the layers
    ethernet_layer = Ether(dst=SRC_MAC, src=DST_MAC)
    ip_layer = IP(src=SRC_IP, dst=DST_IP)
    tcp_layer = TCP(sport=DST_PORT, dport=1010)
    payload = Raw(load=sys.argv[1])

    complete_packet = ethernet_layer/ip_layer/tcp_layer/payload

    wrpcap(PCAP_NAME, complete_packet)

if __name__ == "__main__":
    main()
