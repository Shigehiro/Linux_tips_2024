# Load Balancing DNS Traffic with L3 DSR using LVS (IP-in-IP)

- [Load Balancing DNS Traffic with L3 DSR using LVS (IP-in-IP)](#load-balancing-dns-traffic-with-l3-dsr-using-lvs-ip-in-ip)
  - [Description](#description)
  - [Reference](#reference)
  - [Network Topology](#network-topology)
  - [Configure LVS](#configure-lvs)
  - [Configure DNS Servers](#configure-dns-servers)
  - [Confirmation](#confirmation)

## Description

Here's how to configure L3 DSR with IPIP using LVS (Linux Virtual Server).

## Reference

- [Virtual Server via IP Tunneling](http://www.linuxvirtualserver.org/VS-IPTunneling.html)
- [7. LVS-DR](https://docs.huihoo.com/hpc-cluster/linux-virtual-server/HOWTO/LVS-HOWTO.LVS-DR.html)
- [8. LVS-Tun](https://docs.huihoo.com/hpc-cluster/linux-virtual-server/HOWTO/LVS-HOWTO.LVS-Tun.html)
- [IPVS Using IPIP Tunnel](https://ppan-brian.medium.com/ipvs-using-ipip-tunnel-ca180c7f4fd8)
- [Chapter 9. Configuring IP tunnels](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/9/html/configuring_and_managing_networking/configuring-ip-tunnels_configuring-and-managing-networking)
- https://nileshgr.com/2014/06/27/load-balancing-linux-virtual-server-via-tunneling/
- `man ipvsadm` 

## Network Topology

```
RIP : Real IP
* : Requests
** : Responses

                  Client 192.168.50.10
                    |
                    | ^
                    | |**5
                    |             **4              
                    |            <---                  
192.168.50.0/24     |-----------------------------------
                    |                                  | ^
              *1 |  |                                  | | **3
                 v  |                                  | 
                    |                                  |
                    |                                  | 
 VIP:192.168.50.100 |                                  |
                  eth0 192.168.50.253(RIP)             |
                   LVS                                 |
                  eth1 192.168.51.253(RIP)             |
                  tun0 (10.0.0.253/24)                 |
                    |                                  |
                    |                                  |
                    |                                  |
              *2 |  |                                  | 
                 v  |                                  | 
                    |                                  |
192.168.51.0/24     |                                  |
                    |                                  |
                    |                                  |
                  192.168.51.254(RIP)                  |
                    eth2                               |
                   VyOS eth1 192.168.50.254(RIP)--------
                    eth3
                  192.168.52.254(RIP)    --->
                    |                    **2
                    |               
              *3 |  |                       
                 v  |                       
                    |               
                    |               
                    | ^        
                    | | **1        
                    |         
192.168.52.0/24     |
                    |--------------------------------
              *4 |  |                               |
                 v  |                               |
                    DNS Server01(unbound)        DNS Server02(unbound)
                    192.168.52.100(RIP)          192.168.52.101(RIP)
                    tun0(VIP 192.168.50.100)     tun0(VIP 192.168.50.100)

```

<br>VyOS has three networks, 192.168.50.254(eth1), 192.168.51.254(eth2) and 192.168.52.254(eth3)

- Requests
  - Client -> VIP LVS -> VyOS -> Server0[1-2]
  - `*1 -> *2 -> *3 -> *4`
- Responses
  - Server0[1-2] -> VyOS -> Client 
  - The servers return responses directly
  - `**1 -> **2 -> **3 -> **4 -> **5`

All nodes are running as Virtual Machine under KVM.

## Configure LVS

VIP : 192.168.50.100<br>

On the LVS:<br>

```
[root@lvs ~]# dnf install -y ipvsadm  
```

```
[root@lvs ~]# ip -4 a s
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    altname enp1s0
    inet 192.168.50.253/24 brd 192.168.50.255 scope global noprefixroute eth0
       valid_lft forever preferred_lft forever
3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    altname enp7s0
    inet 192.168.51.253/24 brd 192.168.51.255 scope global noprefixroute eth1
       valid_lft forever preferred_lft forever
```

<br>Configure VIP as secondary address on the front NIC,eth0.
```
[root@lvs ~]# nmcli con mod eth0 +ipv4.addresses 192.168.50.100/24
[root@lvs ~]# nmcli device reapply eth0

[root@lvs ~]# ip -4 a s eth0
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    altname enp1s0
    inet 192.168.50.253/24 brd 192.168.50.255 scope global noprefixroute eth0
       valid_lft forever preferred_lft forever
    inet 192.168.50.100/24 brd 192.168.50.255 scope global secondary noprefixroute eth0
       valid_lft forever preferred_lft forever
```

Configure IP tunneling:<br>
```
# tunneling between LVS and server01
nmcli connection add type ip-tunnel ip-tunnel.mode ipip con-name tun0 ifname tun0 remote 192.168.52.100 local 192.168.51.253
nmcli connection modify tun0 ipv4.addresses '10.0.0.253/24'
nmcli connection modify tun0 ipv4.method manual
nmcli con up tun0 
```

```
# tunneling between LVS and server02
nmcli connection add type ip-tunnel ip-tunnel.mode ipip con-name tun1 ifname tun1 remote 192.168.52.101 local 192.168.51.253
nmcli connection modify tun1 ipv4.addresses '10.0.0.253/24'
nmcli connection modify tun1 ipv4.method manual
nmcli con up tun1
```

```
# ip -4 a s
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    altname enp1s0
    inet 192.168.50.253/24 brd 192.168.50.255 scope global noprefixroute eth0
       valid_lft forever preferred_lft forever
    inet 192.168.50.100/32 scope global noprefixroute eth0
       valid_lft forever preferred_lft forever
3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    altname enp7s0
    inet 192.168.51.253/24 brd 192.168.51.255 scope global noprefixroute eth1
       valid_lft forever preferred_lft forever
5: tun1@NONE: <POINTOPOINT,NOARP,UP,LOWER_UP> mtu 1480 qdisc noqueue state UNKNOWN group default qlen 1000
    inet 10.0.0.253/24 brd 10.0.0.255 scope global noprefixroute tun1
       valid_lft forever preferred_lft forever
6: tun0@NONE: <POINTOPOINT,NOARP,UP,LOWER_UP> mtu 1480 qdisc noqueue state UNKNOWN group default qlen 1000
    inet 10.0.0.253/24 brd 10.0.0.255 scope global noprefixroute tun0
       valid_lft forever preferred_lft forever
# 
```

<br>You do not need to turn on IP forwarding on the LVS.<br>
```
# cat /proc/sys/net/ipv4/ip_forward
0
```

<br>Configure LVS:
```
[root@lvs ~]# systemctl is-active ipvsadm.service 
inactive
```

```
# cat /etc/sysconfig/ipvsadm
-A -t 192.168.50.100:53 -s rr
-a -t 192.168.50.100:53 -r 192.168.52.100:53 -i -w 1 --tun-type ipip
-a -t 192.168.50.100:53 -r 192.168.52.101:53 -i -w 1 --tun-type ipip
-A -u 192.168.50.100:53 -s rr
-a -u 192.168.50.100:53 -r 192.168.52.100:53 -i -w 1 --tun-type ipip
-a -u 192.168.50.100:53 -r 192.168.52.101:53 -i -w 1 --tun-type ipip
```

Add the static route to the DNS servers.
```
[root@lvs ~]# nmcli con mod eth1 ipv4.routes "192.168.52.0/24 192.168.51.254"
[root@lvs ~]# systemctl restart NetworkManager

[root@lvs ~]# ping 192.168.52.101 -c1
PING 192.168.52.101 (192.168.52.101) 56(84) bytes of data.
64 bytes from 192.168.52.101: icmp_seq=1 ttl=63 time=0.425 ms

--- 192.168.52.101 ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 0.425/0.425/0.425/0.000 ms
[root@lvs ~]# 
```

Start LVS:
```
[root@lvs ~]# systemctl start ipvsadm.service 
[root@lvs ~]# systemctl is-active ipvsadm.service 
active
```

## Configure DNS Servers

On the server01:<br>
Configure VIP on the tunnel device,tun0.
```
nmcli connection add type ip-tunnel ip-tunnel.mode ipip con-name tun0 ifname tun0 remote 192.168.51.253 local 192.168.52.100
nmcli connection modify tun0 ipv4.addresses '192.168.50.100/32'
nmcli con modify tun0 ipv4.method manual 
nmcli connection up tun0
```

<br>/etc/sysctl.d/ipip_dsr.conf 
```
# cat /etc/sysctl.d/ipip_dsr.conf 
# enable ip forwarding
net.ipv4.ip_forward=1

# arp settings
net.ipv4.conf.all.arp_ignore=1
net.ipv4.conf.all.arp_announce=2
net.ipv4.conf.tun0.arp_ignore=1
net.ipv4.conf.tun0.arp_announce=2

# loose mode on rp_filter (reverse packet filtering)
# allow packets came from other interface (src ip) 
net.ipv4.conf.tun0.rp_filter=2
```

<br>Reflect the kernel parameters
```
# sysctl -p /etc/sysctl.d/ipip_dsr.conf
```

On the server02:
```
nmcli connection add type ip-tunnel ip-tunnel.mode ipip con-name tun0 ifname tun0 remote 192.168.51.253 local 192.168.52.101
nmcli connection modify tun0 ipv4.addresses '192.168.50.100/32'
nmcli con modify tun0 ipv4.method manual 
nmcli connection up tun0
```

<br>/etc/sysctl.d/ipip_dsr.conf 
```
# enable ip forwarding
net.ipv4.ip_forward=1

# arp settings
net.ipv4.conf.all.arp_ignore=1
net.ipv4.conf.all.arp_announce=2
net.ipv4.conf.tun0.arp_ignore=1
net.ipv4.conf.tun0.arp_announce=2

# loose mode on rp_filter (reverse packet filtering)
# allow packets came from other interface (src ip) 
net.ipv4.conf.tun0.rp_filter=2
```

<br>Reflect the kernel parameters
```
# sysctl -p /etc/sysctl.d/ipip_dsr.conf
```

Start unbound
```
# grep "interface:" /etc/unbound/unbound.conf |grep -v '#'
        interface: 192.168.50.100
        interface: 127.0.0.1
```

```
# systemctl restart unbound
```

## Confirmation

On the client:
```
[root@c01 ~]# while true;do dig @192.168.50.100 version.bind chaos txt +short +retries=0 +timeout=5;sleep 1;done
"unbound 1.16.2"
"Akamai Vantio CacheServe zzz"
"unbound 1.16.2"
"Akamai Vantio CacheServe zzz"
"unbound 1.16.2"
"Akamai Vantio CacheServe zzz"
```

On the LVS:
```
[root@lvs ~]# ipvsadm -ln
IP Virtual Server version 1.2.1 (size=4096)
Prot LocalAddress:Port Scheduler Flags
  -> RemoteAddress:Port           Forward Weight ActiveConn InActConn
TCP  192.168.50.100:53 rr
  -> 192.168.52.100:53            Tunnel  1      0          3         
  -> 192.168.52.101:53            Tunnel  1      0          3         
UDP  192.168.50.100:53 rr
  -> 192.168.52.100:53            Tunnel  1      0          57        
  -> 192.168.52.101:53            Tunnel  1      0          57        
[root@lvs ~]# 
```

Here is a capture data collected on the LVS on eth1.<br>
You can see only requests traffic from the client.
```
[root@lvs ~]# timeout 5 tcpdump -nn -i eth1 ip
dropped privs to tcpdump
tcpdump: verbose output suppressed, use -v[v]... for full protocol decode
listening on eth1, link-type EN10MB (Ethernet), snapshot length 262144 bytes
12:21:05.531658 IP 192.168.51.253 > 192.168.52.101: IP 192.168.50.10.38263 > 192.168.50.100.53: 46986+ [1au] TXT CHAOS? version.bind. (53)
12:21:06.558242 IP 192.168.51.253 > 192.168.52.100: IP 192.168.50.10.51398 > 192.168.50.100.53: 31590+ [1au] TXT CHAOS? version.bind. (53)
12:21:07.586011 IP 192.168.51.253 > 192.168.52.101: IP 192.168.50.10.50918 > 192.168.50.100.53: 18762+ [1au] TXT CHAOS? version.bind. (53)
12:21:08.612489 IP 192.168.51.253 > 192.168.52.100: IP 192.168.50.10.58705 > 192.168.50.100.53: 14518+ [1au] TXT CHAOS? version.bind. (53)
12:21:09.638273 IP 192.168.51.253 > 192.168.52.101: IP 192.168.50.10.39132 > 192.168.50.100.53: 42059+ [1au] TXT CHAOS? version.bind. (53)
```

The Line 1 is the outer IP header and the line 2 is the inner IP header.(IP-in-IP)
```
[root@lvs ~]# tshark -nn -r eth1.cap -V -Y '(frame.number==1)'|grep "Internet Protocol Version 4.*"|cat -n
Running as user "root" and group "root". This could be dangerous.
     1  Internet Protocol Version 4, Src: 192.168.51.253, Dst: 192.168.52.100
     2  Internet Protocol Version 4, Src: 192.168.50.10, Dst: 192.168.50.100
```
