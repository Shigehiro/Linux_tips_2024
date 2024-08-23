# Load-Balance DNS Traffic with Anycast BGP ECMP

- [Load-Balance DNS Traffic with Anycast BGP ECMP](#load-balance-dns-traffic-with-anycast-bgp-ecmp)
- [Description](#description)
- [Reference](#reference)
  - [Network Topology](#network-topology)
  - [Configure DNS Servers](#configure-dns-servers)
    - [Configure anycast IP on the loopback interface](#configure-anycast-ip-on-the-loopback-interface)
    - [Install FRR](#install-frr)
    - [Configure FRR](#configure-frr)
  - [Configure VyOS](#configure-vyos)
  - [Confirmation](#confirmation)

# Description

Here is how to configure DNS Anycast with BGP.

# Reference

- [DNS Anycast: Using BGP for DNS High-Availability](https://yetiops.net/posts/anycast-bgp/)
- [FRRouting User Guide](https://docs.frrouting.org/en/latest/)
- [FRR and Anycast](https://www.unixdude.net/posts/2021/Mar/11/frr-and-anycast/)
- [frr-anycast](https://github.com/dunielpls/frr-anycast)
- https://github.com/FRRouting/frr/issues/7249
- https://gist.github.com/bufadu/0c3ba661c141a2176cd048f65430ae8d
- [Adding More ECMP and Health Checking To Anycast Lab](https://www.jasonvanpatten.com/2019/05/19/adding-more-ecmp-and-health-checking-to-anycast-lab/)

## Network Topology

All nodes are running as virtual machines under KVM.
```
         10.0.100.0/24                   10.0.101.0/24
                              
Three Clients ---------- eth1 VyOS eth2 -------- DNS servers(dns01, dns02)
```

Here is IP address of each node.
- client0[1-3] : 10.0.100.1[1-3]
- VyOS : 10.0.100.245, 10.0.101.254
- dns01 : 10.0.101.10
- dns02 : 10.0.101.11
- Anycast IP : 169.254.0.1/32

<br>Here is AS number:
- VyOS : 64512
- dns01, dns02 : 64513

```
$ show version |head -1
Version:          VyOS 1.5-rolling-202408210022
```

DNS servers.
```
# cat /etc/rocky-release ; uname -ri 
Rocky Linux release 9.4 (Blue Onyx)
5.14.0-427.31.1.el9_4.x86_64 x86_64
```

## Configure DNS Servers

### Configure anycast IP on the loopback interface

[How do I manage the "lo" loopback interface using NetworkManager?](https://access.redhat.com/solutions/2108251)

On the all DNS servers:
```
ansible -i inventory.ini all -m shell -a "nmcli con del lo ; nmcli con add connection.id lo connection.type loopback connection.interface-name lo connection.autoconnect yes ; nmcli con mod lo +ipv4.addresses 169.254.0.1/32 ; nmcli device reapply lo"
```

```
ansible -i inventory.ini all -m shell -a 'ip -4 a s lo|grep inet'
bgp-dns02 | CHANGED | rc=0 >>
    inet 127.0.0.1/8 scope host lo
    inet 169.254.0.1/32 scope link lo
bgp-dns01 | CHANGED | rc=0 >>
    inet 127.0.0.1/8 scope host lo
    inet 169.254.0.1/32 scope link lo
```

### Install FRR

Install frr on all DNS servers.
```
ansible -i inventory.ini all -m shell -a 'dnf install -y frr'
```

```
# rpm -qa |grep ^frr
frr-selinux-8.5.3-4.el9.noarch
frr-8.5.3-4.el9.x86_64
```

Enable bgpd
```
ansible -i inventory.ini all -m shell -a "sed s/bgpd=no/bgpd=yes/ /etc/frr/daemons -i"
```

```
# ansible -i inventory.ini all -m shell -a "grep ^bgpd= /etc/frr/daemons"
bgp-dns02 | CHANGED | rc=0 >>
bgpd=yes
bgp-dns01 | CHANGED | rc=0 >>
bgpd=yes
```

Start frr.service
```
ansible -i inventory.ini all -m shell -a 'systemctl enable frr.service --now'
```

```
# ansible -i inventory.ini all -m shell -a 'systemctl is-active frr'
bgp-dns02 | CHANGED | rc=0 >>
active
bgp-dns01 | CHANGED | rc=0 >>
active
```

### Configure FRR

Here is the AS number:
- VyOS : 64512
- dns01 : 64513
- dns02 : 64513

On the dns01:
```
# ansible -i inventory.ini bgp-dns01 -m shell -a 'cat /etc/frr/frr.conf'
bgp-dns01 | CHANGED | rc=0 >>
frr version 8.5.3
frr defaults traditional
hostname bgp-dns01
no ip forwarding
no ipv6 forwarding
!
router bgp 64513
 bgp router-id 10.0.101.10
 neighbor 10.0.101.254 remote-as 64512
 neighbor 10.0.101.254 password password
 neighbor 10.0.101.254 update-source 10.0.101.10
 !
 address-family ipv4 unicast
  network 169.254.0.1/32
  neighbor 10.0.101.254 soft-reconfiguration inbound
  neighbor 10.0.101.254 route-map route-map-from-peers in
  neighbor 10.0.101.254 route-map route-map-to-peers out
 exit-address-family
exit
!
route-map route-map-from-peers permit 9999
exit
!
route-map route-map-to-peers permit 9999
exit
```

On the dns02:
```
# ansible -i inventory.ini bgp-dns02 -m shell -a 'cat /etc/frr/frr.conf'
bgp-dns02 | CHANGED | rc=0 >>
frr version 8.5.3
frr defaults traditional
hostname bgp-dns02
no ip forwarding
no ipv6 forwarding
!
router bgp 64513
 bgp router-id 10.0.101.11
 neighbor 10.0.101.254 remote-as 64512
 neighbor 10.0.101.254 password password
 neighbor 10.0.101.254 update-source 10.0.101.11
 !
 address-family ipv4 unicast
  network 169.254.0.1/32
  neighbor 10.0.101.254 soft-reconfiguration inbound
  neighbor 10.0.101.254 route-map route-map-from-peers in
  neighbor 10.0.101.254 route-map route-map-to-peers out
 exit-address-family
exit
!
route-map route-map-from-peers permit 9999
exit
!
route-map route-map-to-peers permit 9999
exit
!

```

## Configure VyOS

```
$ show version |head -1
Version:          VyOS 1.5-rolling-202408210022
```

```
vyos@bgp-vyos01:~$ show configuration commands | egrep 'policy|protocols.*bgp|sysctl'
set policy prefix-list AS64513-IN rule 10 action 'permit'
set policy prefix-list AS64513-IN rule 10 prefix '169.254.0.1/32'
set policy prefix-list AS64513-OUT rule 10 action 'deny'
set policy prefix-list AS64513-OUT rule 10 prefix '169.254.0.1/32'
set policy route-map AS64513-IN rule 10 action 'permit'
set policy route-map AS64513-IN rule 10 match ip address prefix-list 'AS64513-IN'
set policy route-map AS64513-IN rule 20 action 'deny'
set policy route-map AS64513-OUT rule 10 action 'deny'
set policy route-map AS64513-OUT rule 10 match ip address prefix-list 'AS64513-OUT'
set policy route-map AS64513-OUT rule 20 action 'permit'
set protocols bgp address-family ipv4-unicast maximum-paths ebgp '8'
set protocols bgp address-family ipv4-unicast maximum-paths ibgp '8'
set protocols bgp neighbor 10.0.101.10 peer-group 'group01'
set protocols bgp neighbor 10.0.101.11 peer-group 'group01'
set protocols bgp parameters bestpath as-path multipath-relax
set protocols bgp peer-group group01 address-family ipv4-unicast route-map export 'AS64513-OUT'
set protocols bgp peer-group group01 address-family ipv4-unicast route-map import 'AS64513-IN'
set protocols bgp peer-group group01 address-family ipv4-unicast soft-reconfiguration inbound
set protocols bgp peer-group group01 password 'password'
set protocols bgp peer-group group01 remote-as '64513'
set protocols bgp peer-group group01 update-source '10.0.101.254'
set protocols bgp system-as '64512'
set system sysctl parameter net.ipv4.fib_multipath_hash_policy value '1'
```

```
vyos@bgp-vyos01# show system sysctl parameter
 parameter net.ipv4.fib_multipath_hash_policy {
     value 1
 }
[edit]
```

## Confirmation

On the VyOS
```
$ ss -tanp |grep 179
LISTEN 0      4096           0.0.0.0:179         0.0.0.0:*                                  
ESTAB  0      0         10.0.101.254:179     10.0.101.10:42695                              
ESTAB  0      0         10.0.101.254:179     10.0.101.11:32955                              
LISTEN 0      4096              [::]:179            [::]:*    
```

On the dns01
```
[root@bgp-dns01 ~]# vtysh 

Hello, this is FRRouting (version 8.5.3).
Copyright 1996-2005 Kunihiro Ishiguro, et al.

bgp-dns01# show bgp summary 

IPv4 Unicast Summary (VRF default):
BGP router identifier 10.0.101.10, local AS number 64513 vrf-id 0
BGP table version 1
RIB entries 1, using 192 bytes of memory
Peers 1, using 725 KiB of memory

Neighbor        V         AS   MsgRcvd   MsgSent   TblVer  InQ OutQ  Up/Down State/PfxRcd   PfxSnt Desc
10.0.101.254    4      64512        14        12        0    0    0 00:04:20            0        1 N/A

Total number of neighbors 1
```

On the VyOS
```
vyos@bgp-vyos01:~$ show ip route bgp
Codes: K - kernel route, C - connected, S - static, R - RIP,
       O - OSPF, I - IS-IS, B - BGP, E - EIGRP, N - NHRP,
       T - Table, v - VNC, V - VNC-Direct, A - Babel, F - PBR,
       f - OpenFabric,
       > - selected route, * - FIB route, q - queued, r - rejected, b - backup
       t - trapped, o - offload failure

B>* 169.254.0.1/32 [20/0] via 10.0.101.10, eth2, weight 1, 01:26:26
  *                       via 10.0.101.11, eth2, weight 1, 01:26:26
```

```
vyos@bgp-vyos01:~$ show bgp ipv4
BGP table version is 12, local router ID is 10.0.102.254, vrf id 0
Default local pref 100, local AS 64512
Status codes:  s suppressed, d damped, h history, * valid, > best, = multipath,
               i internal, r RIB-failure, S Stale, R Removed
Nexthop codes: @NNN nexthop's vrf id, < announce-nh-self
Origin codes:  i - IGP, e - EGP, ? - incomplete
RPKI validation codes: V valid, I invalid, N Not found

    Network          Next Hop            Metric LocPrf Weight Path
 *= 169.254.0.1/32   10.0.101.11              0             0 64513 i
 *>                  10.0.101.10              0             0 64513 i

Displayed  1 routes and 2 total paths
vyos@bgp-vyos01:~$          
```

Send DNS queries from the three clients.<br>
```
[root@bgp-client01 ~]# for i in $(seq 1 3);do ansible -i inventory.ini all -m shell -a 'dig @169.254.0.1 version.bind chaos txt +short' ;done
bgp-client01 | CHANGED | rc=0 >>
"dns02"
bgp-client03 | CHANGED | rc=0 >>
"dns02"
bgp-client02 | CHANGED | rc=0 >>
"dns01"
bgp-client01 | CHANGED | rc=0 >>
"dns01"
bgp-client03 | CHANGED | rc=0 >>
"dns02"
bgp-client02 | CHANGED | rc=0 >>
"dns02"
bgp-client01 | CHANGED | rc=0 >>
"dns02"
bgp-client03 | CHANGED | rc=0 >>
"dns02"
bgp-client02 | CHANGED | rc=0 >>
"dns02"
[root@bgp-client01 ~]# 
```