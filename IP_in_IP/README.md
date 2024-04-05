# Configure IP in IP 
- [Configure IP in IP](#configure-ip-in-ip)
  - [Description](#description)
  - [Reference](#reference)
  - [Network Topology](#network-topology)
  - [Configure IP in IP](#configure-ip-in-ip-1)
  - [Capture data collected on the r01](#capture-data-collected-on-the-r01)

## Description

Here is how to configure IP in IP on CentOS Stream 9.

## Reference

[9.1. Configuring an IPIP tunnel using nmcli to encapsulate IPv4 traffic in IPv4 packets](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/9/html/configuring_and_managing_networking/configuring-ip-tunnels_configuring-and-managing-networking#configuring-an-ipip-tunnel-using-nmcli-to-encapsulate--ipv4-traffic-in-ipv4-packets_configuring-ip-tunnels)

## Network Topology

All nodes are running as Virtual Machin under KVM.
```
            c01
            | 10.10
            |
            | 10.0.10.0/24
            |
            | eth0 10.100
            r01 (tun0 10.10) ------|
            | eth1 2.100           |
            |                      |
            | 172.31.2.0/24        |
            |                      |
            | 2.254                | 192.168.10.0/28 (tun0)
            vyos                   |
            | 3.254                |
            |                      |
            | 172.31.3.0/24        |
            |                      |
            | eth0 3.100           |
            r02 (tun0 10.11) ------|
            | eth1 20.100
            |
            | 10.0.20.0/24
            |
            | 20.10
            c02
```

## Configure IP in IP

Before configuring IP in IP on the r01 and r02.

c01(c02) can not commnicate with c02(c01).
```
# c01 -> c02
[root@c01 ~]# ping 10.0.20.10 -W1 -c1
PING 10.0.20.10 (10.0.20.10) 56(84) bytes of data.

--- 10.0.20.10 ping statistics ---
1 packets transmitted, 0 received, 100% packet loss, time 0ms

# c02 -> c01
[root@c02 ~]# ping 10.0.10.10 -W1 -c1
PING 10.0.10.10 (10.0.10.10) 56(84) bytes of data.

--- 10.0.10.10 ping statistics ---
1 packets transmitted, 0 received, 100% packet loss, time 0ms

# r01 -> c02
[root@r01 ~]# ping 10.0.20.10 -W1 -c1
PING 10.0.20.10 (10.0.20.10) 56(84) bytes of data.

--- 10.0.20.10 ping statistics ---
1 packets transmitted, 0 received, 100% packet loss, time 0ms
[root@r01 ~]# 

# r02 -> c01
[root@r02 ~]# ping -W1 -c1 10.0.10.10
PING 10.0.10.10 (10.0.10.10) 56(84) bytes of data.

--- 10.0.10.10 ping statistics ---
1 packets transmitted, 0 received, 100% packet loss, time 0ms
```

<br>On the r01:
```
nmcli connection add type ip-tunnel ip-tunnel.mode ipip con-name tun0 ifname tun0 remote 172.31.3.100 local 172.31.2.100
nmcli connection modify tun0 ipv4.addresses '192.168.10.10/28'
nmcli connection modify tun0 ipv4.method manual
nmcli connection modify tun0 +ipv4.routes "10.0.20.0/24 192.168.10.11"
nmcli connection up tun0
```

```
# grep ^"net.ipv4" /etc/sysctl.conf 
net.ipv4.ip_forward=1


# cat /proc/sys/net/ipv4/ip_forward
1
```

```
[root@r01 ~]# ip -4 a s
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    altname enp1s0
    inet 10.0.10.100/24 brd 10.0.10.255 scope global noprefixroute eth0
       valid_lft forever preferred_lft forever
3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    altname enp7s0
    inet 172.31.2.100/24 brd 172.31.2.255 scope global noprefixroute eth1
       valid_lft forever preferred_lft forever
8: tun0@NONE: <POINTOPOINT,NOARP,UP,LOWER_UP> mtu 1480 qdisc noqueue state UNKNOWN group default qlen 1000
    inet 192.168.10.10/28 brd 192.168.10.15 scope global noprefixroute tun0
       valid_lft forever preferred_lft forever
[root@r01 ~]# 
[root@r01 ~]# ip r
default via 172.31.2.254 dev eth1 proto static metric 101 
10.0.10.0/24 dev eth0 proto kernel scope link src 10.0.10.100 metric 100 
10.0.20.0/24 via 192.168.10.11 dev tun0 proto static metric 675 
172.31.2.0/24 dev eth1 proto kernel scope link src 172.31.2.100 metric 101 
192.168.10.0/28 dev tun0 proto kernel scope link src 192.168.10.10 metric 675 
[root@r01 ~]# 
```

<br>On the r02:
```
nmcli connection add type ip-tunnel ip-tunnel.mode ipip con-name tun0 ifname tun0 remote 172.31.2.100 local 172.31.3.100
nmcli connection modify tun0 ipv4.addresses '192.168.10.11/28'
nmcli connection modify tun0 ipv4.method manual
nmcli connection modify tun0 +ipv4.routes "10.0.10.0/24 192.168.10.10"
nmcli connection up tun0
```

```
# grep ^"net.ipv4" /etc/sysctl.conf 
net.ipv4.ip_forward=1

# cat /proc/sys/net/ipv4/ip_forward
1
```

```
[root@r02 ~]# ip -4 a s
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    altname enp1s0
    inet 172.31.3.100/24 brd 172.31.3.255 scope global noprefixroute eth0
       valid_lft forever preferred_lft forever
3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    altname enp7s0
    inet 10.0.20.100/24 brd 10.0.20.255 scope global noprefixroute eth1
       valid_lft forever preferred_lft forever
7: tun0@NONE: <POINTOPOINT,NOARP,UP,LOWER_UP> mtu 1480 qdisc noqueue state UNKNOWN group default qlen 1000
    inet 192.168.10.11/28 brd 192.168.10.15 scope global noprefixroute tun0
       valid_lft forever preferred_lft forever

[root@r02 ~]# ip r
default via 172.31.3.254 dev eth0 proto static metric 100 
10.0.10.0/24 via 192.168.10.10 dev tun0 proto static metric 675 
10.0.20.0/24 dev eth1 proto kernel scope link src 10.0.20.100 metric 101 
172.31.3.0/24 dev eth0 proto kernel scope link src 172.31.3.100 metric 100 
192.168.10.0/28 dev tun0 proto kernel scope link src 192.168.10.11 metric 675 
[root@r02 ~]# 
```

<br>Send ping from c1 to c2:
```
[root@c01 ~]# ping 10.0.20.10 -c3
PING 10.0.20.10 (10.0.20.10) 56(84) bytes of data.
64 bytes from 10.0.20.10: icmp_seq=1 ttl=62 time=1.30 ms
64 bytes from 10.0.20.10: icmp_seq=2 ttl=62 time=1.94 ms
64 bytes from 10.0.20.10: icmp_seq=3 ttl=62 time=1.96 ms

--- 10.0.20.10 ping statistics ---
3 packets transmitted, 3 received, 0% packet loss, time 2003ms
rtt min/avg/max/mdev = 1.296/1.729/1.956/0.306 ms
[root@c01 ~]# 
```

## Capture data collected on the r01

Here are capture files on r01 for each NIC.<br>
You can see IP packet is encapsulated in IP packet.<br>
```
[root@r01 ~]# ls *.cap
r01_eth0.cap  r01_eth1.cap  r01_tun0.cap

[root@r01 ~]# ip -4 a s
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    altname enp1s0
    inet 10.0.10.100/24 brd 10.0.10.255 scope global noprefixroute eth0
       valid_lft forever preferred_lft forever
3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    altname enp7s0
    inet 172.31.2.100/24 brd 172.31.2.255 scope global noprefixroute eth1
       valid_lft forever preferred_lft forever
8: tun0@NONE: <POINTOPOINT,NOARP,UP,LOWER_UP> mtu 1480 qdisc noqueue state UNKNOWN group default qlen 1000
    inet 192.168.10.10/28 brd 192.168.10.15 scope global noprefixroute tun0
       valid_lft forever preferred_lft forever
[root@r01 ~]# 
```

<br>eth0
```
[root@r01 ~]# tshark -nn -r r01_eth0.cap |head -2
Running as user "root" and group "root". This could be dangerous.
    1   0.000000   10.0.10.10 → 10.0.20.10   ICMP 98 Echo (ping) request  id=0x0012, seq=1198/44548, ttl=64
    2   0.001392   10.0.20.10 → 10.0.10.10   ICMP 98 Echo (ping) reply    id=0x0012, seq=1198/44548, ttl=62 (request in 1)
[root@r01 ~]# 
```

```
[root@r01 ~]# tshark -n -r r01_eth0.cap -V -Y '(frame.number==1)' |grep ^"Internet.*4" -A3
Running as user "root" and group "root". This could be dangerous.
Internet Protocol Version 4, Src: 10.0.10.10, Dst: 10.0.20.10
    0100 .... = Version: 4
    .... 0101 = Header Length: 20 bytes (5)
    Differentiated Services Field: 0x00 (DSCP: CS0, ECN: Not-ECT)
```

<br>tun0
```
[root@r01 ~]# tshark -n -r r01_tun0.cap |head -2
Running as user "root" and group "root". This could be dangerous.
    1   0.000000   10.0.10.10 → 10.0.20.10   ICMP 84 Echo (ping) request  id=0x0012, seq=1920/32775, ttl=63
    2   0.001312   10.0.20.10 → 10.0.10.10   ICMP 84 Echo (ping) reply    id=0x0012, seq=1920/32775, ttl=63 (request in 1)
[root@r01 ~]# 
```

```
[root@r01 ~]# tshark -n -r r01_tun0.cap -V -Y '(frame.number==1)' |grep ^"Internet.*4" -A3
Running as user "root" and group "root". This could be dangerous.
Internet Protocol Version 4, Src: 10.0.10.10, Dst: 10.0.20.10
    0100 .... = Version: 4
    .... 0101 = Header Length: 20 bytes (5)
    Differentiated Services Field: 0x00 (DSCP: CS0, ECN: Not-ECT)
```

<br>eth1(IP in IP)

```
[root@r01 ~]# tshark -nn -r r01_eth1.cap |grep ICMP
Running as user "root" and group "root". This could be dangerous.
   13   0.487838   10.0.10.10 → 10.0.20.10   ICMP 118 Echo (ping) request  id=0x0014, seq=42/10752, ttl=63
   14   0.489321   10.0.20.10 → 10.0.10.10   ICMP 118 Echo (ping) reply    id=0x0014, seq=42/10752, ttl=63 (request in 13)
   17   1.489594   10.0.10.10 → 10.0.20.10   ICMP 118 Echo (ping) request  id=0x0014, seq=43/11008, ttl=63
   18   1.491138   10.0.20.10 → 10.0.10.10   ICMP 118 Echo (ping) reply    id=0x0014, seq=43/11008, ttl=63 (request in 17)
```

<br>You can see IP packet is encapsulated in IP packet.<br>
Also see [Wiki IP in IP](https://en.wikipedia.org/wiki/IP_in_IP) and [rfc2003](https://datatracker.ietf.org/doc/html/rfc2003)
```
[root@r01 ~]# tshark -n -r r01_eth1.cap -V -Y '(frame.number==13)' |grep ^"Internet.*4" -A3 -n
Running as user "root" and group "root". This could be dangerous.
25:Internet Protocol Version 4, Src: 172.31.2.100, Dst: 172.31.3.100
26-    0100 .... = Version: 4
27-    .... 0101 = Header Length: 20 bytes (5)
28-    Differentiated Services Field: 0x00 (DSCP: CS0, ECN: Not-ECT)
--
44:Internet Protocol Version 4, Src: 10.0.10.10, Dst: 10.0.20.10
45-    0100 .... = Version: 4
46-    .... 0101 = Header Length: 20 bytes (5)
47-    Differentiated Services Field: 0x00 (DSCP: CS0, ECN: Not-ECT)
```