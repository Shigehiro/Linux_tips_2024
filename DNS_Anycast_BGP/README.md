# DNS Anycast with BGP

# Description

Here is how to configure DNS Anycast with BGP.

# Reference

- [DNS Anycast: Using BGP for DNS High-Availability](https://yetiops.net/posts/anycast-bgp/)
- [Anycast DNS - Using BGP](http://ddiguru.com/blog/anycast-dns-part-5-using-bgp)
- [FRRouting User Guide](https://docs.frrouting.org/en/latest/)
- [FRR and Anycast](https://www.unixdude.net/posts/2021/Mar/11/frr-and-anycast/)
- [frr-anycast](https://github.com/dunielpls/frr-anycast)
- [BGP + BFD config question](https://forum.vyos.io/t/bgp-bfd-config-question/13119/1)
- [Getting Started to BGP](https://darin.web.id/sdn/configure-bgp-on-vyos-for-vsphere)
- https://github.com/FRRouting/frr/issues/7249

## Network Topology

All nodes are running as virtual machines under KVM.
```
                                  10.0.101.0/24
        10.0.100.0/24          |------ DNS servers(dns01,dns02)
                               |
                              eth2
Client -----------------eth1  VyOS 
                              eth3
                               |
                               |------ DNS servers(dns03,dns04)
                                  10.0.102.0/24
```

Here is IP address of each node.
- client : 10.0.100.10
- VyOS : 10.0.100.245, 10.0.101.254, 10.0.102.254
- dns01 : 10.0.101.10
- dns02 : 10.0.101.11
- dns03 : 10.0.102.12
- dns04 : 10.0.102.13
- Anycast IP : 169.254.0.1

<br>Here is AS number:
- VyOS : 64512
- dns01 : 64513
- dns02 : 64514
- dns03 : 64515
- dns04 : 64516

## Configure DNS Servers

### Configure anycast IP on the loopback interface

[How do I manage the "lo" loopback interface using NetworkManager?](https://access.redhat.com/solutions/2108251)

On the all DNS servers:
```
# nmcli con del lo
# nmcli con add connection.id lo connection.type loopback connection.interface-name lo connection.autoconnect yes
# nmcli con mod lo +ipv4.addresses 169.254.0.1/32
# nmcli device reapply lo 
```

```
# ansible -i inventory.ini all -m shell -a 'ip -4 a s lo |grep inet'
bgp-dns04 | CHANGED | rc=0 >>
    inet 127.0.0.1/8 scope host lo
    inet 169.254.0.1/32 scope global lo
bgp-dns02 | CHANGED | rc=0 >>
    inet 127.0.0.1/8 scope host lo
    inet 169.254.0.1/32 scope global lo
bgp-dns03 | CHANGED | rc=0 >>
    inet 127.0.0.1/8 scope host lo
    inet 169.254.0.1/32 scope global lo
bgp-dns01 | CHANGED | rc=0 >>
    inet 127.0.0.1/8 scope host lo
    inet 169.254.0.1/32 scope global lo
#
```

### Install FRR

Install frr on all DNS servers.
```
# ansible -i inventory.ini all -m shell -a 'dnf install -y frr'
```

```
# rpm -qa |grep ^frr
frr-selinux-8.5.3-4.el9.noarch
frr-8.5.3-4.el9.x86_64
```

Enable bgpd
```
# ansible -i inventory.ini all -m shell -a "sed s/bgpd=no/bgpd=yes/ /etc/frr/daemons -i"
```

```
# ansible -i inventory.ini all -m shell -a "grep ^bgp /etc/frr/daemons "
bgp-dns01 | CHANGED | rc=0 >>
bgpd=yes
bgpd_options="   -A 127.0.0.1"
bgp-dns02 | CHANGED | rc=0 >>
bgpd=yes
bgpd_options="   -A 127.0.0.1"
bgp-dns04 | CHANGED | rc=0 >>
bgpd=yes
bgpd_options="   -A 127.0.0.1"
bgp-dns03 | CHANGED | rc=0 >>
bgpd=yes
bgpd_options="   -A 127.0.0.1"
```

Start frr.service
```
# ansible -i inventory.ini all -m shell -a 'systemctl start frr.service'
# ansible -i inventory.ini all -m shell -a 'systemctl is-active frr.service'
```

### Configure BGP

Here is AS number:
- VyOS : 64512
- dns01 : 64513
- dns02 : 64514
- dns03 : 64515
- dns04 : 64516

On the dns01:
```
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
!
```

## Configure VyOS

```
$ show version |head -1
Version:          VyOS 1.5-rolling-202408210022
```

```
set interfaces ethernet eth0 address 'dhcp'
set interfaces ethernet eth1 address '10.0.100.254/24'
set interfaces ethernet eth1 description 'client net'
set interfaces ethernet eth2 address '10.0.101.254/24'
set interfaces ethernet eth2 description 'dns server seg 01'
set interfaces ethernet eth3 address '10.0.102.254/24'
set interfaces ethernet eth3 description 'dns server seg 02'
set interfaces loopback lo
set nat source rule 1 outbound-interface name 'eth0'
set nat source rule 1 source address '10.0.100.0/24'
set nat source rule 1 translation address 'masquerade'
set nat source rule 2 outbound-interface name 'eth0'
set nat source rule 2 source address '10.0.101.0/24'
set nat source rule 2 translation address 'masquerade'
set nat source rule 3 outbound-interface name 'eth0'
set nat source rule 3 source address '10.0.102.0/24'
set nat source rule 3 translation address 'masquerade'
set policy route-map anycast rule 10 action 'permit'
set policy route-map anycast rule 10 set as-path prepend '64513 64514 64515 64516'
set protocols bgp address-family ipv4-unicast
set protocols bgp neighbor 10.0.101.10 address-family ipv4-unicast route-map import 'anycast'
set protocols bgp neighbor 10.0.101.10 address-family ipv4-unicast soft-reconfiguration inbound
set protocols bgp neighbor 10.0.101.10 password 'password'
set protocols bgp neighbor 10.0.101.10 remote-as '64513'
set protocols bgp neighbor 10.0.101.11 address-family ipv4-unicast route-map import 'anycast'
set protocols bgp neighbor 10.0.101.11 address-family ipv4-unicast soft-reconfiguration inbound
set protocols bgp neighbor 10.0.101.11 password 'password'
set protocols bgp neighbor 10.0.101.11 remote-as '64514'
set protocols bgp neighbor 10.0.102.12 address-family ipv4-unicast route-map import 'anycast'
set protocols bgp neighbor 10.0.102.12 address-family ipv4-unicast soft-reconfiguration inbound
set protocols bgp neighbor 10.0.102.12 password 'password'
set protocols bgp neighbor 10.0.102.12 remote-as '64515'
set protocols bgp neighbor 10.0.102.13 address-family ipv4-unicast route-map import 'anycast'
set protocols bgp neighbor 10.0.102.13 address-family ipv4-unicast soft-reconfiguration inbound
set protocols bgp neighbor 10.0.102.13 password 'password'
set protocols bgp neighbor 10.0.102.13 remote-as '64516'
set protocols bgp system-as '64512'
```

## Confirmation

On the dns01
```
[root@bgp-dns01 ~]# vtysh
bgp-dns01# show bgp summary

IPv4 Unicast Summary (VRF default):
BGP router identifier 10.0.101.10, local AS number 64513 vrf-id 0
BGP table version 1
RIB entries 1, using 192 bytes of memory
Peers 1, using 725 KiB of memory

Neighbor        V         AS   MsgRcvd   MsgSent   TblVer  InQ OutQ  Up/Down State/PfxRcd   PfxSnt Desc
10.0.101.254    4      64512        21        20        0    0    0 00:16:32            0        1 N/A

Total number of neighbors 1
bgp-dns01#
```

On the VyOS
```
vyos@bgp-vyos01:~$ show bgp ipv4
BGP table version is 11, local router ID is 192.168.122.125, vrf id 0
Default local pref 100, local AS 64512
Status codes:  s suppressed, d damped, h history, * valid, > best, = multipath,
               i internal, r RIB-failure, S Stale, R Removed
Nexthop codes: @NNN nexthop's vrf id, < announce-nh-self
Origin codes:  i - IGP, e - EGP, ? - incomplete
RPKI validation codes: V valid, I invalid, N Not found

    Network          Next Hop            Metric LocPrf Weight Path
 *  169.254.0.1/32   10.0.102.13              0             0 64513 64514 64515 64516 64516 i
 *                   10.0.102.12              0             0 64513 64514 64515 64516 64515 i
 *                   10.0.101.11              0             0 64513 64514 64515 64516 64514 i
 *>                  10.0.101.10              0             0 64513 64514 64515 64516 64513 i

Displayed  1 routes and 4 total paths
```

Send DNS queries from the client.
```
[root@bgp-client01 ~]# ip r g 169.254.0.1
169.254.0.1 via 10.0.100.254 dev eth0 src 10.0.100.10 uid 0
    cache
```