# Configure SPAN with FD.io VPP

- [Configure SPAN with FD.io VPP](#configure-span-with-fdio-vpp)
  - [Network Topology](#network-topology)
  - [Configure SPAN](#configure-span)
  - [If both the VPP and the capture node are running under KVM and you cannot see wire data on the capture node.](#if-both-the-vpp-and-the-capture-node-are-running-under-kvm-and-you-cannot-see-wire-data-on-the-capture-node)

## Network Topology

All nodes are running as virtual machines under KVM.
```
   Client .10
      | 10.1.0.0/24
      |
      |
      |.254
     VPP .254-----(span network)--- Capture node
      |.254         10.3.0.0/24      .10 
      | 
      |
      |
      | 10.2.0.0/24
      |
      |.10
   DNS server
```

```
# dpkg -l |grep vpp
ii  libvppinfra                      24.06-release                           amd64        Vector Packet Processing--runtime libraries
ii  vpp                              24.06-release                           amd64        Vector Packet Processing--executables
ii  vpp-plugin-core                  24.06-release                           amd64        Vector Packet Processing--runtime core plugins
ii  vpp-plugin-dpdk                  24.06-release                           amd64        Vector Packet Processing--runtime dpdk plugin

# tail -1 /etc/lsb-release 
DISTRIB_DESCRIPTION="Ubuntu 22.04.4 LTS"
```

```
# vppctl show int|grep ^Gigabit
GigabitEthernet7/0/0              1      up          9000/0/0/0     rx packets                    30
GigabitEthernet8/0/0              2      up          9000/0/0/0     rx packets                    31
GigabitEthernet9/0/0              3      up          9000/0/0/0     rx packets                    25

# grep 10.[1-3] /usr/share/vpp/scripts/vpp-config.txt 
set int ip address GigabitEthernet7/0/0 10.1.0.254/24
set int ip address GigabitEthernet8/0/0 10.2.0.254/24
set int ip address GigabitEthernet9/0/0 10.3.0.244/24
```

## Configure SPAN

Reference:
- [Switched Port Analyzer](https://s3-docs.fd.io/vpp/24.10/developer/corefeatures/span_doc.html)
- [Span cli reference](https://s3-docs.fd.io/vpp/24.10/cli-reference/clis/clicmd_src_vnet_span.html)

<br>Configure SPAN:
```
vpp# set interface span GigabitEthernet7/0/0 l2 destination GigabitEthernet9/0/0 rx
vpp# set interface span GigabitEthernet7/0/0 destination GigabitEthernet9/0/0 rx

```

```
vpp# show interface span 
Source                           Destination                       Device       L2
GigabitEthernet7/0/0             GigabitEthernet9/0/0             (    rx) (    rx)
```

```
# grep span /usr/share/vpp/scripts/vpp-config.txt 
set interface span GigabitEthernet7/0/0 l2 destination GigabitEthernet9/0/0 rx
set interface span GigabitEthernet7/0/0 destination GigabitEthernet9/0/0 rx
```

Generate traffic from the client to the server.
```
# for i in $(seq 1 1000);do dig @10.2.0.10 localhost +short;sleep 1;done
```

On the SPAN node:
```
# timeout 3 tcpdump -nn -i enp7s0 port 53
tcpdump: verbose output suppressed, use -v[v]... for full protocol decode
listening on enp7s0, link-type EN10MB (Ethernet), snapshot length 262144 bytes
02:31:57.634800 IP 10.1.0.10.39757 > 10.2.0.10.53: 25585+ [1au] A? localhost. (50)
02:31:58.645322 IP 10.1.0.10.33029 > 10.2.0.10.53: 41445+ [1au] A? localhost. (50)
02:31:59.667582 IP 10.1.0.10.54419 > 10.2.0.10.53: 24697+ [1au] A? localhost. (50)
```

## If both the VPP and the capture node are running under KVM and you cannot see wire data on the capture node.

Try the below.<br>

Here is the capture node:
```
$ sudo virsh domiflist span-zeek01
 Interface   Type      Source    Model    MAC
-------------------------------------------------------------
 vnet8       network   default   virtio   52:54:00:f2:b7:b3
 vnet9       network   no-ip03   virtio   52:54:00:8e:5b:30 # span network ( collect wire data )
```

Here is the vpp node:
```
$ sudo virsh domiflist span-vpp01
 Interface   Type      Source    Model    MAC
-------------------------------------------------------------
 vnet4       network   default   virtio   52:54:00:b9:37:4c
 vnet5       network   no-ip01   virtio   52:54:00:d5:a0:cd
 vnet6       network   no-ip02   virtio   52:54:00:0b:a2:a8
 vnet7       network   no-ip03   virtio   52:54:00:99:f4:93 # span network ( span port )
```

On the KVM host:
```
$ sudo brctl setageing no-ip03 0
$ sudo brctl setfd no-ip03 0
```

You will see wire data on the capture node.<br>
See https://man7.org/linux/man-pages/man8/brctl.8.html.