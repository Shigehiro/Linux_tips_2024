#!/usr/bin/env python3

from scapy.all import *

def convert_dscp_for_scapy(DSCP):
  """Convert DSCP bit for SCAPY"""
  bin_val = (str(bin(DSCP)) + str('00'))
  DSCP_SCAPY = int(bin_val, 2)
  return DSCP_SCAPY

def ipv6_dns_udp(DSCP_SCAPY):
  """Send UDP DNS over IPv6"""
  print("Sent DNS UDP over IPv6")
  l2=Ether()
  l3=IPv6(src="2001:db8:1::c",dst="2001:db8:1::a",tc=DSCP_SCAPY)
  l4=UDP(dport=53)/DNS(rd=1, qd=DNSQR(qname='version.bind',qtype='TXT',qclass='CH'))
  sendp(l2/l3/l4, verbose=False, count=1)

def ipv6_tcp_syn53(DSCP_SCAPY):
  """Send TCP SYN 53 over IPv6"""
  print("Sent TCP 53 SYN over IPv6")
  l2=Ether()
  l3=IPv6(src="2001:db8:1::c",dst="2001:db8:1::a",tc=DSCP_SCAPY)
  l4=TCP(sport=40508,dport=53,flags="S",seq=12345)
  sendp(l2/l3/l4, verbose=False, count=1)

def ipv4_dns_udp(DSCP_SCAPY):
  """Send UDP DNS over IPv4"""
  print("Sent DNS UDP over IPv4")
  l2=Ether()
  l3=IP(src="172.25.2.33",dst="172.25.2.30",tos=DSCP_SCAPY)
  l4=UDP(dport=53)/DNS(rd=1, qd=DNSQR(qname='version.bind',qtype='TXT',qclass='CH'))
  sendp(l2/l3/l4, verbose=False, count=1)

def ipv4_tcp_syn53(DSCP_SCAPY):
  """Send TCP SYN 53 over IPv4"""
  print("Sent TCP 53 SYN over IPv4")
  l2=Ether()
  l3=IP(src="172.25.2.33",dst="172.25.2.30",tos=DSCP_SCAPY)
  l4=TCP(sport=40509,dport=53,flags="S",seq=12345)
  sendp(l2/l3/l4, verbose=False, count=1)

if __name__ == "__main__":
  DSCP_SCAPY = convert_dscp_for_scapy(DSCP=2)
  ipv6_dns_udp(DSCP_SCAPY=DSCP_SCAPY)
  ipv6_tcp_syn53(DSCP_SCAPY)
  ipv4_dns_udp(DSCP_SCAPY=DSCP_SCAPY)
  ipv4_tcp_syn53(DSCP_SCAPY)
