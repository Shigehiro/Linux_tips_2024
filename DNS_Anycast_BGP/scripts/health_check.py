#!/usr/bin/env python3

"""
Add or delete a BGP path based on the result of a DNS health check.
"""

import argparse
import dns.message
import dns.query
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('-q', '--qname', type=str, required=True, help='Specify a query name')
parser.add_argument('-t', '--type', type=str, default='A', help='Specify a query type. Default A')
parser.add_argument('-s', '--server', type=str, default='127.0.0.1', help='Specify a server IP address. Default 127.0.0.1')
parser.add_argument('-a', '--anycast_ip', type=str, required=True, help='Specify an Anycast IP')
parser.add_argument('-as', '--as_number', type=int, required=True, help='Specify a BGP AS number')
args = parser.parse_args()
qname = args.qname
qtype = args.type
server = args.server
anycast_ip = args.anycast_ip
as_number = args.as_number
timeout = 3

def send_query(qname, rdtype, server, protocol='udp'):
    # Construct a query
    q = dns.message.make_query(qname=qname, rdtype=qtype)

    # health check result
    health_result = False

    # Make a UDP query
    if protocol == 'udp':
        try:
            res = dns.query.udp(q, where=server, timeout=timeout)
            health_result = True
        except Exception as _:
            pass
    # Make a TCP query
    elif protocol == 'tcp':
        try:
            res = dns.query.tcp(q, where=server, timeout=timeout)
            health_result = True
        except Exception as _:
            pass

    return health_result

def add_bgp_path():
    vtysh_cmd = '/usr/bin/vtysh -f /tmp/vtysh.conf'

    command_text = f"""
    router bgp {as_number}
    address-family ipv4 unicast
    network {anycast_ip}/32
    exit
    exit
    exit
    write memory
    exit
    """

    with open('/tmp/vtysh.conf', 'w') as f:
        f.write(command_text)
    subprocess.run(vtysh_cmd.split(), stdout=subprocess.PIPE, stderr = subprocess.PIPE)

def del_bgp_path():
    vtysh_cmd = '/usr/bin/vtysh -f /tmp/vtysh.conf'

    command_text = f"""
    router bgp {as_number}
    address-family ipv4 unicast
    no network {anycast_ip}/32
    exit
    exit
    exit
    write memory
    exit
    """

    with open('/tmp/vtysh.conf', 'w') as f:
        f.write(command_text)
    subprocess.run(vtysh_cmd.split(), stdout=subprocess.PIPE, stderr = subprocess.PIPE)

if __name__ == '__main__':
    udp_result = False
    tcp_result = False

    # Try the UDP health check
    udp_result = send_query(qname=qname, rdtype=qtype, server=server)

    # If the UDP health check is successful, try the TCP health check.
    if udp_result:
        tcp_result = send_query(qname=qname, rdtype=qtype, server=server, protocol='tcp')

    # Add the anycast IP in BGP
    if udp_result and tcp_result:
        add_bgp_path()
    # Delete the anycast IP from BGP
    else:
        del_bgp_path()