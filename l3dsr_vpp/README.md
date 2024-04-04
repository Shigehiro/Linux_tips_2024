# L3 DSR based on DSCP with vpp

- [L3 DSR based on DSCP with vpp](#l3-dsr-based-on-dscp-with-vpp)
  - [Description](#description)
  - [About vpp](#about-vpp)
  - [Install vpp](#install-vpp)
  - [Configure L3 DSR](#configure-l3-dsr)
    - [Client requests](#client-requests)
    - [Server responses](#server-responses)
    - [Configure vpp for L3 DSR](#configure-vpp-for-l3-dsr)

## Description

Here is how to configure L3 DSR based on DSCP with vpp

## About vpp

See https://s3-docs.fd.io/vpp/24.06/index.html

## Install vpp

Reference: https://wiki.fd.io/view/VPP/Installing_VPP_binaries_from_packages#Intro

Launch a VM for vpp. (three vNICs)<br>
One for the management, two for vpp.
```
# tail -1 /etc/lsb-release
DISTRIB_DESCRIPTION="Ubuntu 22.04.4 LTS"
```

Configure the management network.
```
# cat /etc/netplan/00-installer-config.yaml
# This is the network config written by 'subiquity'
network:
  ethernets:
    enp1s0:
      dhcp4: true
  version: 2
```

```
# netplan apply
```

```
# ip a
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever
2: enp1s0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 52:54:00:af:1a:f7 brd ff:ff:ff:ff:ff:ff
    inet 192.168.100.219/24 metric 100 brd 192.168.100.255 scope global dynamic enp1s0
       valid_lft 2541sec preferred_lft 2541sec
    inet6 fe80::5054:ff:feaf:1af7/64 scope link
       valid_lft forever preferred_lft forever
3: enp7s0: <BROADCAST,MULTICAST> mtu 1500 qdisc noop state DOWN group default qlen 1000
    link/ether 52:54:00:ec:a9:d1 brd ff:ff:ff:ff:ff:ff
4: enp8s0: <BROADCAST,MULTICAST> mtu 1500 qdisc noop state DOWN group default qlen 1000
    link/ether 52:54:00:d5:6c:cd brd ff:ff:ff:ff:ff:ff
```

<br>Add the repo
```
# curl -s https://packagecloud.io/install/repositories/fdio/master/script.deb.sh | sudo bash
```

<br>Install vpp
```
# apt-get install vpp vpp-plugin-core vpp-plugin-dpdk vpp-dbg vpp-dev -y
```

<br>Installed version
```
# dpkg -l |grep vpp
ii  libvppinfra                            24.06-rc0~168-gb48325100~b1256          amd64        Vector Packet Processing--runtime libraries
ii  libvppinfra-dev                        24.06-rc0~168-gb48325100~b1256          amd64        Vector Packet Processing--runtime libraries
ii  vpp                                    24.06-rc0~168-gb48325100~b1256          amd64        Vector Packet Processing--executables
ii  vpp-dbg                                24.06-rc0~168-gb48325100~b1256          amd64        Vector Packet Processing--debug symbols
ii  vpp-dev                                24.06-rc0~168-gb48325100~b1256          amd64        Vector Packet Processing--development support
ii  vpp-plugin-core                        24.06-rc0~168-gb48325100~b1256          amd64        Vector Packet Processing--runtime core plugins
ii  vpp-plugin-dpdk                        24.06-rc0~168-gb48325100~b1256          amd64        Vector Packet Processing--runtime dpdk plugin
```

<br>Reboot the OS
```
# systemctl reboot
```

```
# systemctl is-active vpp
active
```

<br>Check interfaces recognized by vpp.
```
# vppctl show int
              Name               Idx    State  MTU (L3/IP4/IP6/MPLS)     Counter          Count
GigabitEthernet7/0/0              1     down         9000/0/0/0
GigabitEthernet8/0/0              2     down         9000/0/0/0
local0                            0     down          0/0/0/0
#
```

<br>0000:07:00.0 and 0000:08:00.0 are managed by vpp.
```
# dmesg | grep -E 'vpp|enp1s0'
[    1.638850] virtio_net virtio0 enp1s0: renamed from eth0 # management network. this is for accessing the internet
[   92.148989] vfio-pci 0000:07:00.0: vfio-noiommu device opened by user (vpp:1053) # managed by vpp
[   92.396569] vfio-pci 0000:08:00.0: vfio-noiommu device opened by user (vpp:1053) # managed by vpp
```

<br>Configure IP addresses.
```
# vppctl set int ip address GigabitEthernet7/0/0 172.25.0.10/24
# vppctl set int ip address GigabitEthernet8/0/0 172.25.1.10/24
# vppctl set int state GigabitEthernet7/0/0 up
# vppctl set int state GigabitEthernet8/0/0 up
```

```
# vppctl show int address
GigabitEthernet7/0/0 (up):
  L3 172.25.0.10/24
GigabitEthernet8/0/0 (up):
  L3 172.25.1.10/24
local0 (dn):
```

Send ping from the vpp box to the other nodes.
```
# vppctl ping 172.25.0.20
116 bytes from 172.25.0.20: icmp_seq=2 ttl=64 time=.4945 ms

# vppctl ping 172.25.1.20
116 bytes from 172.25.1.20: icmp_seq=2 ttl=64 time=.3527 ms
```

## Configure L3 DSR

Reference: https://docs.fd.io/vpp/24.06/developer/plugins/lb.html<br>

Here is the network topology I used.
```
    172.25.0.0/24     172.25.1.0/24      172.25.2.0/24
client ---L2SW------ vpp -------------L3 SW ------ two servers
    0.30   |     0.10   1.10       1.20 |  2.20     2.30, 2.31
           |                            |
           ------------------------------ 
                                   0.20(172.25.0.20)

VIP for LB : 172.26.0.10
```

The L3 SW has three networks, 172.25.[0-2].20<br>

### Client requests

Client -> L2SW -> vpp -> L3SW -> two servers
  
Client -> vpp
```
Src IP : 172.25.0.30
Dst IP : 172.26.0.10 (VIP)
```

vpp -> two servers
```
Src IP : 172.25.0.30
Dst IP : 172.25.2.30 or 31 ( vpp will add specified DSCP number )
```

### Server responses

Two servers -> L3 SW -> Client
```
Src IP : 172.26.0.10 ( The server should rewrite its srcIP as VIP based on DSCP )
Dst IP : 172.25.0.30
```

### Configure vpp for L3 DSR

<br>lb_plugin.so must be loaded to use Load Balancing.
```
# vppctl show plugins |grep lb
 66. lb_plugin.so                             24.02-release                    Load Balancer (LB)
```

<br>Edit the config.
```
# grep -v '#' /etc/vpp/startup.conf |grep -v ^$|grep plugins -A4
plugins {
        plugin default { enable }
        plugin dpdk_plugin.so { enable }
        plugin lb_plugin.so { enable }
}
```

<br>Restart vpp to reflect the config.
```
# systemctl restart vpp.service
```

<br>After restarting the vpp, IP addresses setttings will be cleared, so re-configure IP addresses.
```
# vppctl set int ip address GigabitEthernet7/0/0 172.25.0.10/24
# vppctl set int ip address GigabitEthernet8/0/0 172.25.1.10/24
# vppctl set int state GigabitEthernet7/0/0 up
# vppctl set int state GigabitEthernet8/0/0 up
```

```
# vppctl show int address
GigabitEthernet7/0/0 (up):
  L3 172.25.0.10/24
GigabitEthernet8/0/0 (up):
  L3 172.25.1.10/24
local0 (dn):
```

<br>Configure static routes if needed.
```
# vppctl ip route add 172.25.2.0/24 via 172.25.1.20 GigabitEthernet8/0/0
```

<br>Configure L3 DSR
```
vppctl lb conf timeout 3
vppctl lb vip 172.26.0.10/24 encap l3dsr dscp 2 port 0 new_len 32
vppctl lb as 172.26.0.10/24 port 0 172.25.2.30 172.25.2.31
```

```
# vppctl show lb vip verbose
 ip4-l3dsr [1] 172.26.0.0/24
  new_size:32
  dscp:2
  counters:
    packet from existing sessions: 22
    first session packet: 46
    untracked packet: 0
    no server configured: 0
  #as:2
    172.25.2.31 16 buckets   28 flows  dpo:21 used
    172.25.2.30 16 buckets   18 flows  dpo:22 used
```

<br>On the client, send DNS queries.<br>

Confiure static routes if needed.( )
```
# nmcli con show eth1 |grep ^ipv4.routes
ipv4.routes:                            { ip = 172.25.2.0/24, nh = 172.25.0.20 }; { ip = 172.26.0.10/32, nh = 172.25.0.10 }
```

```
# for i in $(seq 1 50);do dig @172.26.0.10 www.google.com;sleep 3;done
```

<br>Here is a capture data collected on the server.
```
# tshark -nn -r udp53.pcap -Y '(frame.number==1)'
Running as user "root" and group "root". This could be dangerous.
    1   0.000000  172.25.0.30 → 172.25.2.30  DNS 97 Standard query 0x1312 A www.google.com OPT
```

<br>Looking at the line 5, you could see the DSCP is 2.
```
# tshark -nn -r udp53.pcap -V -Y '(frame.number==1)' | grep ^'Internet Protocol' -A10|cat -n
Running as user "root" and group "root". This could be dangerous.
     1  Internet Protocol Version 4, Src: 172.25.0.30, Dst: 172.25.2.30
     2      0100 .... = Version: 4
     3      .... 0101 = Header Length: 20 bytes (5)
     4      Differentiated Services Field: 0x08 (DSCP: Unknown, ECN: Not-ECT)
     5          0000 10.. = Differentiated Services Codepoint: Unknown (2)
     6          .... ..00 = Explicit Congestion Notification: Not ECN-Capable Transport (0)
     7      Total Length: 83
     8      Identification: 0xe43b (58427)
     9      Flags: 0x00
    10          0... .... = Reserved bit: Not set
    11          .0.. .... = Don't fragment: Not set
```

<br>Here is the vpp config I used.
```
# cat configure_vpp_l3dsr.sh
#!/bin/sh

echo "configure IP"
vppctl set int ip address GigabitEthernet7/0/0 172.25.0.10/24
vppctl set int ip address GigabitEthernet8/0/0 172.25.1.10/24
vppctl set int state GigabitEthernet7/0/0 up
vppctl set int state GigabitEthernet8/0/0 up

echo "Add static route"
vppctl ip route add 172.25.2.0/24 via 172.25.1.20 GigabitEthernet8/0/0

echo "Configure L3 DSR with DSCP"
vppctl lb conf timeout 3
vppctl lb vip 172.26.0.10/24 encap l3dsr dscp 2 port 0 new_len 32
vppctl lb as 172.26.0.10/24 port 0 172.25.2.30 172.25.2.31
```