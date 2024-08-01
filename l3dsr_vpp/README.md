# 1. L3 DSR based on DSCP with vpp

- [1. L3 DSR based on DSCP with vpp](#1-l3-dsr-based-on-dscp-with-vpp)
  - [1.1. Description](#11-description)
  - [1.2. Tested Network Toplogy](#12-tested-network-toplogy)
  - [1.3. Reference](#13-reference)
  - [1.4. About vpp](#14-about-vpp)
  - [1.5. Install vpp](#15-install-vpp)
  - [1.6. Configure L3 DSR](#16-configure-l3-dsr)
    - [1.6.1. Client requests](#161-client-requests)
    - [1.6.2. Server responses](#162-server-responses)
    - [1.6.3. Configure vpp for L3 DSR](#163-configure-vpp-for-l3-dsr)
  - [1.7. Configure the server to rewrite its SrcIP based on DSCP](#17-configure-the-server-to-rewrite-its-srcip-based-on-dscp)
    - [1.7.1. Install DSCP kernel module](#171-install-dscp-kernel-module)
      - [1.7.1.1. Rocky Linux 8.9](#1711-rocky-linux-89)
      - [1.7.1.2. Rocky Linux 9.3](#1712-rocky-linux-93)
  - [1.8. Confirm L3DSR works](#18-confirm-l3dsr-works)
  - [1.9. L3 DSR DSCP Kernel module build results](#19-l3-dsr-dscp-kernel-module-build-results)
  - [1.10. Confirm whether the DSCP kernel module works with both IPv4 and IPv6 using Python Scapy](#110-confirm-whether-the-dscp-kernel-module-works-with-both-ipv4-and-ipv6-using-python-scapy)
  - [1.11. How to load vpp configuration from a text file when starting vpp](#111-how-to-load-vpp-configuration-from-a-text-file-when-starting-vpp)
  - [1.12. How to manage loopback interface with nmcli(NetworkManager)](#112-how-to-manage-loopback-interface-with-nmclinetworkmanager)
  - [1.13. How to configure L3DSR DSCP rules with firewalld](#113-how-to-configure-l3dsr-dscp-rules-with-firewalld)


## 1.1. Description

Here is how to configure L3 DSR based on DSCP with vpp

## 1.2. Tested Network Toplogy

All nodes are running as Virtual Machine under KVM.
```
    172.25.0.0/24        172.25.1.0/24      172.25.2.0/24
client ---L2SW------ vpp ------------- vyos ------ two servers
    0.30   |     0.10   1.10       1.20 |  2.20     2.30, 2.31
           |                            |
           ------------------------------ 
                                   0.20(172.25.0.20. vyos ip)

VIP for LB : 172.26.0.10
```

## 1.3. Reference

- https://events19.linuxfoundation.org/wp-content/uploads/2018/07/ONS.NA_.2019.VPP_LB_public.pdf
- https://www.loadbalancer.org/blog/yahoos-l3-direct-server-return-an-alternative-to-lvs-tun-explored/
- https://github.com/yahoo/l3dsr

## 1.4. About vpp

See https://s3-docs.fd.io/vpp/24.06/index.html

## 1.5. Install vpp

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

## 1.6. Configure L3 DSR

Reference: https://docs.fd.io/vpp/24.06/developer/plugins/lb.html<br>

```
    172.25.0.0/24        172.25.1.0/24      172.25.2.0/24
client ---L2SW------ vpp ------------- vyos ------ two servers
    0.30   |     0.10   1.10       1.20 |  2.20     2.30, 2.31
           |                            |
           ------------------------------ 
                                   0.20(172.25.0.20)

VIP for LB : 172.26.0.10
```

The L3 SW has three networks, 172.25.[0-2].20<br>

### 1.6.1. Client requests

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

### 1.6.2. Server responses

Two servers -> L3 SW -> Client
```
Src IP : 172.26.0.10 ( The server should rewrite its srcIP as VIP based on DSCP )
Dst IP : 172.25.0.30
```

### 1.6.3. Configure vpp for L3 DSR

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

<br>Configure L3 DSR<br>
You do not need to configure VIPs on VPP interfaces.
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

Confiure static routes if needed.
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

## 1.7. Configure the server to rewrite its SrcIP based on DSCP

### 1.7.1. Install DSCP kernel module

#### 1.7.1.1. Rocky Linux 8.9

```
# cat /etc/rocky-release
Rocky Linux release 8.9 (Green Obsidian)
# uname -ri
4.18.0-513.18.1.el8_9.x86_64 x86_64

```

```
dnf groupinstall "Development Tools" -y
```

```
dnf install iptables-devel iptables-utils -y
```

```
git clone https://github.com/yahoo/l3dsr.git
```

```
cd l3dsr/linux/iptables-daddr/
```

```
make
```

```
make libdir=/usr/lib64 install
```

```
# echo "options xt_DADDR table=mangle" > /etc/modprobe.d/xt_DADDR.conf
# cat /etc/modprobe.d/xt_DADDR.conf
options xt_DADDR table=mangle
```

```
systemctl reboot
```

Make sure the kernel module xt_DADDR.ko exists
```
# modinfo xt_DADDR
filename:       /lib/modules/4.18.0-513.18.1.el8_9.x86_64/extra/xt_DADDR.ko
alias:          ip6t_DADDR
alias:          ipt_DADDR
license:        GPL
description:    Xtables: destination address modification
author:         Verizon Media <linux-kernel-team@verizonmedia.com>
rhelversion:    8.9
srcversion:     450E188B765B10AD5B5CFA4
depends:
name:           xt_DADDR
vermagic:       4.18.0-513.18.1.el8_9.x86_64 SMP mod_unload modversions
parm:           table:type of table (default: raw) (charp)
```

```
# ip addr add 172.26.0.10/32 dev lo label lo:1
```

```
# iptables -t mangle -A INPUT -m dscp --dscp 2 -j DADDR --set-daddr=172.26.0.10
```

```
# iptables -t mangle -L -n
Chain PREROUTING (policy ACCEPT)
target     prot opt source               destination

Chain INPUT (policy ACCEPT)
target     prot opt source               destination
DADDR      all  --  0.0.0.0/0            0.0.0.0/0            DSCP match 0x02 DADDR set 172.26.0.10

Chain FORWARD (policy ACCEPT)
target     prot opt source               destination

Chain OUTPUT (policy ACCEPT)
target     prot opt source               destination

Chain POSTROUTING (policy ACCEPT)
target     prot opt source               destination
```

```
# lsmod |grep xt_
xt_DADDR               16384  1
xt_dscp                16384  1
```

#### 1.7.1.2. Rocky Linux 9.3

```
# cat /etc/rocky-release
Rocky Linux release 9.3 (Blue Onyx)
# uname -ri
5.14.0-362.24.1.el9_3.x86_64 x86_64
```

```
# cd l3dsr/linux/iptables-daddr/
# make
# make libdir=/usr/lib64 install
# echo 'options xt_DADDR table=mangle' > /etc/modprobe.d/xt_DADDR.conf
# systemctl reboot
```

```
# modinfo xt_DADDR
filename:       /lib/modules/5.14.0-362.24.1.el9_3.x86_64/extra/xt_DADDR.ko
alias:          ip6t_DADDR
alias:          ipt_DADDR
license:        GPL
description:    Xtables: destination address modification
author:         Verizon Media <linux-kernel-team@verizonmedia.com>
rhelversion:    9.3
srcversion:     FACE9732EE5DD30EEEBD549
depends:
retpoline:      Y
name:           xt_DADDR
vermagic:       5.14.0-362.24.1.el9_3.x86_64 SMP preempt mod_unload modversions
parm:           table:type of table (default: raw) (charp)
```

```
# ip addr add 172.26.0.10/32 dev lo label lo:1

# ip -4 a s lo
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet 172.26.0.10/32 scope global lo:1
       valid_lft forever preferred_lft forever

# iptables -t mangle -A INPUT -m dscp --dscp 2 -j DADDR --set-daddr=172.26.0.10
```

```
# iptables -t mangle -L -n
Chain PREROUTING (policy ACCEPT)
target     prot opt source               destination

Chain INPUT (policy ACCEPT)
target     prot opt source               destination
DADDR      all  --  0.0.0.0/0            0.0.0.0/0            DSCP match 0x02 DADDR set 172.26.0.10

Chain FORWARD (policy ACCEPT)
target     prot opt source               destination

Chain OUTPUT (policy ACCEPT)
target     prot opt source               destination

Chain POSTROUTING (policy ACCEPT)
target     prot opt source               destination
```

## 1.8. Confirm L3DSR works

Send DNS queries from the client.<br>
UDP 53.
```
# dig @172.26.0.10 www.google.com

; <<>> DiG 9.16.23-RH <<>> @172.26.0.10 www.google.com
; (1 server found)
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 18977
;; flags: qr rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1

;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags:; udp: 512
;; QUESTION SECTION:
;www.google.com.                        IN      A

;; ANSWER SECTION:
www.google.com.         300     IN      A       142.250.196.132

;; Query time: 49 msec
;; SERVER: 172.26.0.10#53(172.26.0.10)
;; WHEN: Fri Apr 05 05:17:18 EDT 2024
;; MSG SIZE  rcvd: 59
```

TCP 53
```
# dig @172.26.0.10 www.google.com +tcp

; <<>> DiG 9.16.23-RH <<>> @172.26.0.10 www.google.com +tcp
; (1 server found)
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 64707
;; flags: qr rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1

;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags:; udp: 512
;; QUESTION SECTION:
;www.google.com.                        IN      A

;; ANSWER SECTION:
www.google.com.         300     IN      A       142.250.196.132

;; Query time: 180 msec
;; SERVER: 172.26.0.10#53(172.26.0.10)
;; WHEN: Fri Apr 05 05:18:21 EDT 2024
;; MSG SIZE  rcvd: 59
```

<br>On the vpp:
```
# vppctl show lb vip verbose
 ip4-l3dsr [1] 172.26.0.0/24
  new_size:32
  dscp:2
  counters:
    packet from existing sessions: 5
    first session packet: 287
    untracked packet: 0
    no server configured: 0
  #as:2
    172.25.2.31 16 buckets   45 flows  dpo:20 used
    172.25.2.30 16 buckets   53 flows  dpo:21 used
```

Here is a capture data collected on the server.<br>
No1. vpp -> the server<br>
No2. the server -> client

```
# tshark -nn -r udp53.cap |grep 24a2
Running as user "root" and group "root". This could be dangerous.
    1   0.000000  172.25.0.30 → 172.25.2.31  DNS 97 Standard query 0x24a2 A www.google.com OPT
    2   0.002509  172.26.0.10 → 172.25.0.30  DNS 101 Standard query response 0x24a2 A www.google.com A 142.250.196.132 OPT
```

```
# tshark -nn -r udp53.cap -Y '(frame.number==1)' -V |grep ^Internet -A5
Running as user "root" and group "root". This could be dangerous.
Internet Protocol Version 4, Src: 172.25.0.30, Dst: 172.25.2.31
    0100 .... = Version: 4
    .... 0101 = Header Length: 20 bytes (5)
    Differentiated Services Field: 0x08 (DSCP: Unknown, ECN: Not-ECT)
        0000 10.. = Differentiated Services Codepoint: Unknown (2)
        .... ..00 = Explicit Congestion Notification: Not ECN-Capable Transport (0)
```

```
# tshark -nn -r udp53.cap -Y '(frame.number==2)' -V |grep ^Internet -A5
Running as user "root" and group "root". This could be dangerous.
Internet Protocol Version 4, Src: 172.26.0.10, Dst: 172.25.0.30
    0100 .... = Version: 4
    .... 0101 = Header Length: 20 bytes (5)
    Differentiated Services Field: 0x00 (DSCP: CS0, ECN: Not-ECT)
        0000 00.. = Differentiated Services Codepoint: Default (0)
        .... ..00 = Explicit Congestion Notification: Not ECN-Capable Transport (0)
```

<br>Here is a capture of data collected on the server for TCP port 53.
```
# tshark  -n -r tcp53.cap -Y '(tcp.port==59995)'
Running as user "root" and group "root". This could be dangerous.
    1   0.000000  172.25.0.30 → 172.25.2.31  TCP 74 59995 → 53 [SYN] Seq=0 Win=64240 Len=0 MSS=1460 SACK_PERM=1 TSval=1532374090 TSecr=0 WS=128
    2   0.000134  172.26.0.10 → 172.25.0.30  TCP 74 53 → 59995 [SYN, ACK] Seq=0 Ack=1 Win=65160 Len=0 MSS=1460 SACK_PERM=1 TSval=3042040255 TSecr=1532374090 WS=128
    3   0.000589  172.25.0.30 → 172.25.2.31  TCP 66 59995 → 53 [ACK] Seq=1 Ack=1 Win=64256 Len=0 TSval=1532374091 TSecr=3042040255
    4   0.003661  172.25.0.30 → 172.25.2.31  DNS 123 Standard query 0x53ee A www.google.com OPT
    5   0.003694  172.26.0.10 → 172.25.0.30  TCP 66 53 → 59995 [ACK] Seq=1 Ack=58 Win=65152 Len=0 TSval=3042040258 TSecr=1532374093
    8   0.054429  172.26.0.10 → 172.25.0.30  DNS 127 Standard query response 0x53ee A www.google.com A 142.250.196.132 OPT
    9   0.055125  172.25.0.30 → 172.25.2.31  TCP 66 59995 → 53 [ACK] Seq=58 Ack=62 Win=64256 Len=0 TSval=1532374145 TSecr=3042040309
   10   0.055490  172.25.0.30 → 172.25.2.31  TCP 66 59995 → 53 [FIN, ACK] Seq=58 Ack=62 Win=64256 Len=0 TSval=1532374146 TSecr=3042040309
   11   0.096435  172.26.0.10 → 172.25.0.30  TCP 66 53 → 59995 [ACK] Seq=62 Ack=59 Win=65152 Len=0 TSval=3042040351 TSecr=1532374146
   12   1.055836  172.26.0.10 → 172.25.0.30  TCP 66 53 → 59995 [FIN, ACK] Seq=62 Ack=59 Win=65152 Len=0 TSval=3042041310 TSecr=1532374146
   13   1.056543  172.25.0.30 → 172.25.2.31  TCP 66 59995 → 53 [ACK] Seq=59 Ack=63 Win=64256 Len=0 TSval=1532375147 TSecr=3042041310
```

```
# tshark -nn -r tcp53.cap -Y '(frame.number==1)' -V |grep ^Internet -A5
Running as user "root" and group "root". This could be dangerous.
Internet Protocol Version 4, Src: 172.25.0.30, Dst: 172.25.2.31
    0100 .... = Version: 4
    .... 0101 = Header Length: 20 bytes (5)
    Differentiated Services Field: 0x08 (DSCP: Unknown, ECN: Not-ECT)
        0000 10.. = Differentiated Services Codepoint: Unknown (2)
        .... ..00 = Explicit Congestion Notification: Not ECN-Capable Transport (0)
```

## 1.9. L3 DSR DSCP Kernel module build results

|OS|Kernel|GCC|Kernel module<br>Git commit ID|Result|
|:---|:---|:---|:---|:---|
|Rocky Linux release 8.9|4.18.0-513.18.1.el8_9.x86_64|8.5.0 20210514 (Red Hat 8.5.0-20)|Master branch<br>8928361|OK|
|Rocky Linux release 8.10|4.18.0-553.el8_10.x86_64 x86_64|8.5.0 20210514 (Red Hat 8.5.0-22)|Master branch<br>8928361|OK|
|Rocky Linux release 9.3 |5.14.0-362.24.1.el9_3.0.1.x86_64|11.4.1 20230605 (Red Hat 11.4.1-2)|Master branch<br>8928361|OK|
|Rocky Linux release 9.4 |5.14.0-427.16.1.el9_4.x86_64|11.4.1 20231218 (Red Hat 11.4.1-3)|Master branch<br>8928361|Failed(*)|
|CentOS Stream release 8|4.18.0-552.el8.x86_64|8.5.0 20210514 (Red Hat 8.5.0-21)|Master branch<br>8928361|OK|
|CentOS Stream release 9|5.14.0-435.el9.x86_64|11.4.1 20231218 (Red Hat 11.4.1-3)|Master branch<br>8928361|Failed(*)|
|Fedora release 39|6.8.4-200.fc39.x86_64|13.2.1 20240316 (Red Hat 13.2.1-7)|Master branch<br>8928361|Failed(*)|

(*) Apply this [Address issue 23 with constructor patch to library #24](https://github.com/yahoo/l3dsr/pull/24)<br>
I was able to build the kernel moduels after applying that.

## 1.10. Confirm whether the DSCP kernel module works with both IPv4 and IPv6 using Python Scapy

On the server, configure iptables|ip6tables to re-write its Src address:
```
ip addr add 172.26.0.10/32 dev lo label lo:1
ip addr add 2001:db8:1::100/128 dev lo label lo:2
ip6tables -t mangle -A INPUT -m dscp --dscp 2 -j DADDR --set-daddr=2001:db8:1::100
iptables -t mangle -A INPUT -m dscp --dscp 2 -j DADDR --set-daddr=172.26.0.10
```

On the Scapy node, configure IPv4 and IPv6
```
nmcli con mod eth0 ipv6.method manual ipv6.addresses 2001:db8:1::c/64
```

On the server, run the tcpdump.
```
# tcpdump -nn -i eth0 port 53 -w port53.cap
```

[Run the script](./send_dns_with_dscp.py)
```
# ./send_dns_with_dscp.py
Sent DNS UDP over IPv6
Sent TCP 53 SYN over IPv6
Sent DNS UDP over IPv4
Sent TCP 53 SYN over IPv4
```

Here is the capture data collected on the server:
- IPv6 UDP(No1,2)
  - Looking at No2, you can see the server re-wrote its Src IP from 2001:db8:1::a to 2001:db8:1::100
- IPv6 TCP SYN 53(No3,4)
- IPv4 UDP(No5,6)
  - Looking at No6, the server re-wrote its Src IP from 172.25.2.30 to 172.26.0.10
- IPv4 TCP SYN 53(No7,8)
```
# tshark -nn -r port53.cap
Running as user "root" and group "root". This could be dangerous.
    1   0.000000 2001:db8:1::c → 2001:db8:1::a DNS 92 Standard query 0x0000 TXT version.bind
    2   0.000206 2001:db8:1::100 → 2001:db8:1::c DNS 111 Standard query response 0x0000 TXT version.bind TXT
    3   0.016484 2001:db8:1::c → 2001:db8:1::a TCP 74 40508 → 53 [SYN] Seq=0 Win=8192 Len=0
    4   0.016535 2001:db8:1::100 → 2001:db8:1::c TCP 78 53 → 40508 [SYN, ACK] Seq=0 Ack=1 Win=28800 Len=0 MSS=1440
    5   0.052722  172.25.2.33 → 172.25.2.30  DNS 72 Standard query 0x0000 TXT version.bind
    6   0.052883  172.26.0.10 → 172.25.2.33  DNS 91 Standard query response 0x0000 TXT version.bind TXT
    7   0.070183  172.25.2.33 → 172.25.2.30  TCP 54 40509 → 53 [SYN] Seq=0 Win=8192 Len=0
    8   0.070224  172.26.0.10 → 172.25.2.33  TCP 58 53 → 40509 [SYN, ACK] Seq=0 Ack=1 Win=29200 Len=0 MSS=1460
```

## 1.11. How to load vpp configuration from a text file when starting vpp

/etc/vpp/startup.conf
```
# grep -E 'unix|startup-config' /etc/vpp/startup.conf
unix {
  startup-config /usr/share/vpp/scripts/vpp-config.txt
```

/usr/share/vpp/scripts/vpp-config.txt
```
# configure interface
set int ip address GigabitEthernet7/0/0 172.25.0.10/24
set int ip address GigabitEthernet8/0/0 172.25.1.10/24
set int state GigabitEthernet7/0/0 up
set int state GigabitEthernet8/0/0 up

# configure static route
ip route add 172.25.2.0/24 via 172.25.1.20 GigabitEthernet8/0/0

# configure load balancer plugin
lb conf timeout 3
lb vip 172.26.0.10/24 encap l3dsr dscp 2 po
```

## 1.12. How to manage loopback interface with nmcli(NetworkManager)

See [How do I manage the "lo" loopback interface using NetworkManager?](https://access.redhat.com/solutions/2108251)

```
mv /etc/sysconfig/network-scripts/ifcfg-lo /root
```

```
nmcli connection reload
```

```
nmcli con add connection.id lo connection.type loopback connection.interface-name lo connection.autoconnect yes
```

```
nmcli connection up lo
```

```
nmcli con mod lo +ipv4.addresses 172.26.0.10/32
```

## 1.13. How to configure L3DSR DSCP rules with firewalld

You may want to disalbe connection tracking regarding TCP/UDP 53.<br>

See [How can I disable connection tracking (conntrack) with firewalld?](https://access.redhat.com/solutions/2991381)

Ensure firewalld is running and the other services, nftables and iptables, are not running.
```
# systemctl is-active firewalld.service nftables.service iptables.service
active
inactive
inactive
```

```
# systemctl is-active firewalld.service
active
```

```
# firewall-cmd --set-default-zone=trusted
```

```
firewall-cmd --permanent --direct --add-rule ipv4 raw PREROUTING 0 -p udp --dport 53 -j NOTRACK
firewall-cmd --permanent --direct --add-rule ipv4 raw PREROUTING 0 -p udp --sport 53 -j NOTRACK
firewall-cmd --permanent --direct --add-rule ipv4 raw PREROUTING 0 -p tcp --dport 53 -j NOTRACK
firewall-cmd --permanent --direct --add-rule ipv4 raw PREROUTING 0 -p tcp --sport 53 -j NOTRACK

firewall-cmd --permanent --direct --add-rule ipv4 raw OUTPUT 0 -p udp --dport 53 -j NOTRACK
firewall-cmd --permanent --direct --add-rule ipv4 raw OUTPUT 0 -p udp --sport 53 -j NOTRACK
firewall-cmd --permanent --direct --add-rule ipv4 raw OUTPUT 0 -p tcp --dport 53 -j NOTRACK
firewall-cmd --permanent --direct --add-rule ipv4 raw OUTPUT 0 -p tcp --sport 53 -j NOTRACK

firewall-cmd --permanent --direct --add-rule ipv4 filter INPUT 0 -p udp --dport 53 -j ACCEPT
firewall-cmd --permanent --direct --add-rule ipv4 filter INPUT 0 -p tcp --dport 53 -j ACCEPT

firewall-cmd --permanent --direct --add-rule ipv4 mangle INPUT 100 -m dscp --dscp 2 -j DADDR --set-daddr=172.26.0.10
```
