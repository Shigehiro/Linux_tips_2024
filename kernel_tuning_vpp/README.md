# 1. Kernel Tuning for VPP

- [1. Kernel Tuning for VPP](#1-kernel-tuning-for-vpp)
  - [1.1. Description](#11-description)
  - [1.2. Reference](#12-reference)
  - [1.3. Testing Environment](#13-testing-environment)
  - [1.4. Tuning Logs](#14-tuning-logs)
    - [1.4.1. CPU tuning](#141-cpu-tuning)
      - [1.4.1.1. Check CPU topology](#1411-check-cpu-topology)
      - [1.4.1.2. Isolcate CPUs with tuned](#1412-isolcate-cpus-with-tuned)
    - [1.4.2. Memory tuning](#142-memory-tuning)
    - [1.4.3. VPP config](#143-vpp-config)
      - [1.4.3.1. DPDK](#1431-dpdk)
      - [1.4.3.2. CPU](#1432-cpu)
    - [1.4.4. VPP show commands](#144-vpp-show-commands)

## 1.1. Description

Here is how tune kernel for VPP.

## 1.2. Reference

- [VPP/How To Optimize Performance (System Tuning)](https://wiki.fd.io/view/VPP/How_To_Optimize_Performance_(System_Tuning))
- [Multi-threading in VPP](https://s3-docs.fd.io/vpp/24.10/developer/corearchitecture/multi_thread.html)
- [Huge Pages](https://fd.io/docs/vpp/v2101/gettingstarted/users/configuring/hugepages.html)
- [Metrics and tools for tuning](https://ubuntu.com/blog/real-time-kernel-tuning)
- [Optimizing RHEL 9 for Real Time for low latency operation](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux_for_real_time/9/html-single/optimizing_rhel_9_for_real_time_for_low_latency_operation/index)

## 1.3. Testing Environment

```
# lsb_release -a;uname -ri
No LSB modules are available.
Distributor ID: Ubuntu
Description:    Ubuntu 24.04 LTS
Release:        24.04
Codename:       noble
6.8.0-39-generic x86_64
```

```
# numactl -H
available: 2 nodes (0-1)
node 0 cpus: 0 1 2 3 4 5 6 7 8 9 10 11
node 0 size: 32186 MB
node 0 free: 31696 MB
node 1 cpus: 12 13 14 15 16 17 18 19 20 21 22 23
node 1 size: 32207 MB
node 1 free: 31736 MB
node distances:
node   0   1
  0:  10  20
  1:  20  10
```

```
# dpkg -l |grep vpp
ii  libvppinfra                          24.10-rc0~96-ge0e85134a                 amd64        Vector Packet Processing--runtime libraries
ii  libvppinfra-dev                      24.10-rc0~96-ge0e85134a                 amd64        Vector Packet Processing--runtime libraries
ii  vpp                                  24.10-rc0~96-ge0e85134a                 amd64        Vector Packet Processing--executables
ii  vpp-dbg                              24.10-rc0~96-ge0e85134a                 amd64        Vector Packet Processing--debug symbols
ii  vpp-dev                              24.10-rc0~96-ge0e85134a                 amd64        Vector Packet Processing--development support
ii  vpp-plugin-core                      24.10-rc0~96-ge0e85134a                 amd64        Vector Packet Processing--runtime core plugins
ii  vpp-plugin-dpdk                      24.10-rc0~96-ge0e85134a                 amd64        Vector Packet Processing--runtime dpdk plugin
```

## 1.4. Tuning Logs

### 1.4.1. CPU tuning

#### 1.4.1.1. Check CPU topology

VPP has two NUMAs
```
# numactl -H
available: 2 nodes (0-1)
node 0 cpus: 0 1 2 3 4 5 6 7 8 9 10 11
node 0 size: 32186 MB
node 0 free: 30715 MB
node 1 cpus: 12 13 14 15 16 17 18 19 20 21 22 23
node 1 size: 32207 MB
node 1 free: 30903 MB
node distances:
node   0   1
  0:  10  20
  1:  20  10
```

```
# numastat
                           node0           node1
numa_hit                  139149          145143
numa_miss                      0               0
numa_foreign                   0               0
interleave_hit               149             136
local_node                137034          141757
other_node                  2115            3386
```

Here is the siblings information.
The core 0 and the core 1 share the same physical core.
```
# for file in /sys/devices/system/cpu/cpu[0-9]*/topology/thread_siblings_list; do echo -n "$file "; cat $file; done |sort -k2 -n
/sys/devices/system/cpu/cpu0/topology/thread_siblings_list 0-1
/sys/devices/system/cpu/cpu1/topology/thread_siblings_list 0-1
/sys/devices/system/cpu/cpu2/topology/thread_siblings_list 2-3
/sys/devices/system/cpu/cpu3/topology/thread_siblings_list 2-3
/sys/devices/system/cpu/cpu4/topology/thread_siblings_list 4-5
/sys/devices/system/cpu/cpu5/topology/thread_siblings_list 4-5
/sys/devices/system/cpu/cpu6/topology/thread_siblings_list 6-7
/sys/devices/system/cpu/cpu7/topology/thread_siblings_list 6-7
/sys/devices/system/cpu/cpu8/topology/thread_siblings_list 8-9
/sys/devices/system/cpu/cpu9/topology/thread_siblings_list 8-9
/sys/devices/system/cpu/cpu10/topology/thread_siblings_list 10-11
/sys/devices/system/cpu/cpu11/topology/thread_siblings_list 10-11
/sys/devices/system/cpu/cpu12/topology/thread_siblings_list 12-13
/sys/devices/system/cpu/cpu13/topology/thread_siblings_list 12-13
/sys/devices/system/cpu/cpu14/topology/thread_siblings_list 14-15
/sys/devices/system/cpu/cpu15/topology/thread_siblings_list 14-15
/sys/devices/system/cpu/cpu16/topology/thread_siblings_list 16-17
/sys/devices/system/cpu/cpu17/topology/thread_siblings_list 16-17
/sys/devices/system/cpu/cpu18/topology/thread_siblings_list 18-19
/sys/devices/system/cpu/cpu19/topology/thread_siblings_list 18-19
/sys/devices/system/cpu/cpu20/topology/thread_siblings_list 20-21
/sys/devices/system/cpu/cpu21/topology/thread_siblings_list 20-21
/sys/devices/system/cpu/cpu22/topology/thread_siblings_list 22-23
/sys/devices/system/cpu/cpu23/topology/thread_siblings_list 22-23
```

#### 1.4.1.2. Isolcate CPUs with tuned

```
# grep ^isolated /etc/tuned/realtime-variables.conf
isolated_cores=4-19
```

```
# systemctl is-active tuned.service
active
```

```
# tuned-adm profile cpu-partitioning
```

```
# systemctl reboot
```

```
# tuned-adm active
Current active profile: cpu-partitioning
```

```
# cat /proc/cmdline
BOOT_IMAGE=/boot/vmlinuz-6.8.0-39-generic root=UUID=af1698f8-a72d-4304-95c5-d40119d92281 ro console=tty0 console=ttyS0,115200n8 rootdelay=60 splash quiet vt.handoff=7 skew_tick=1 tsc=reliable rcupdate.rcu_normal_after_boot=1 nohz=on nohz_full=4-19 rcu_nocbs=4-19 tuned.non_isolcpus=00f0000f intel_pstate=disable nosoftlockup
```

### 1.4.2. Memory tuning

It seems that hugepages for VPP are already configured in /etc/sysctl.d/80-vpp.conf when installing VPP.
See [Huge Pages](https://fd.io/docs/vpp/v2101/gettingstarted/users/configuring/hugepages.html)

```
# grep -v ^# /etc/sysctl.d/80-vpp.conf |grep -v ^$
vm.nr_hugepages=1024
vm.max_map_count=3096
vm.hugetlb_shm_group=0
kernel.shmmax=2147483648
```

```
# grep -i hugepage /proc/meminfo
AnonHugePages:         0 kB
ShmemHugePages:        0 kB
FileHugePages:         0 kB
HugePages_Total:    1024
HugePages_Free:      980
HugePages_Rsvd:        0
HugePages_Surp:        0
Hugepagesize:       2048 kB
```

### 1.4.3. VPP config

#### 1.4.3.1. DPDK

[The dpdk Section](https://fd.io/docs/vpp/v2101/gettingstarted/users/configuring/startup#the-dpdk-section)

Here is PCI bus info for VPP interface.
```
# lshw -c network

<snip>

  *-network
       description: Ethernet controller
       product: Virtio 1.0 network device
       vendor: Red Hat, Inc.
       physical id: 0
       bus info: pci@0000:07:00.0
       version: 01
       width: 64 bits
       clock: 33MHz
       capabilities: msix pm pciexpress bus_master cap_list rom
       configuration: driver=uio_pci_generic latency=0
       resources: iomemory:38380-3837f irq:22 memory:fdc40000-fdc40fff memory:383800000000-383800003fff memory:fdc00000-fdc3ffff
  *-network
       description: Ethernet controller
       product: Virtio 1.0 network device
       vendor: Red Hat, Inc.
       physical id: 0
       bus info: pci@0000:08:00.0
       version: 01
       width: 64 bits
       clock: 33MHz
       capabilities: msix pm pciexpress bus_master cap_list rom
       configuration: driver=uio_pci_generic latency=0
       resources: iomemory:38300-382ff irq:22 memory:fda40000-fda40fff memory:383000000000-383000003fff memory:fda00000-fda3ffff
```

vpp config(/etc/vpp/startup.conf) for dpdk will be look like this:
```
plugins {
  path /usr/lib/x86_64-linux-gnu/vpp_plugins
  plugin default { enable }
  plugin dpdk_plugin.so { enable }
  plugin lb_plugin.so { enable }
}

dpdk {
  dev 0000:07:00.0 {
    num-rx-queues 2
    num-rx-desc 512
    num-tx-desc 512

   }

  dev 0000:08:00.0 {
    num-rx-queues 2
    num-rx-desc 512
    num-tx-desc 512
   }
}
```

Configure plugins you would like to use.

#### 1.4.3.2. CPU

[The cpu Section](https://fd.io/docs/vpp/v2101/gettingstarted/users/configuring/startup#the-cpu-section)

```
# grep isolcpus /proc/cmdline
BOOT_IMAGE=/boot/vmlinuz-6.8.0-39-generic root=UUID=af1698f8-a72d-4304-95c5-d40119d92281 ro console=tty0 console=ttyS0,115200n8 rootdelay=60 splash quiet vt.handoff=7 skew_tick=1 tsc=reliable rcupdate.rcu_normal_after_boot=1 isolcpus=managed_irq,domain,4-19 intel_pstate=disable nosoftlockup
```

vpp config for CPU.
```
cpu {
  main-core 4
  corelist-workers 6,8,10,12

}

dpdk {
  dev 0000:07:00.0 {
    num-rx-queues 2
    num-rx-desc 512
    num-tx-desc 512

   }

  dev 0000:08:00.0 {
    num-rx-queues 2
    num-rx-desc 512
    num-tx-desc 512
   }
}
```

start the vpp
```
# systemctl restart vpp.service
```

```
# vppctl show hardware-interfaces| grep Gigabit -A5
GigabitEthernet7/0/0               1     up   GigabitEthernet7/0/0
  Link speed: unknown
  RX Queues:
    queue thread         mode
    0     vpp_wk_0 (1)   polling
    1     vpp_wk_1 (2)   polling
--
GigabitEthernet8/0/0               2     up   GigabitEthernet8/0/0
  Link speed: unknown
  RX Queues:
    queue thread         mode
    0     vpp_wk_2 (3)   polling
    1     vpp_wk_3 (4)   polling
```

```
# vppctl show threads
ID     Name                Type        LWP     Sched Policy (Priority)  lcore  Core   Socket State
0      vpp_main                        1330    other (0)                4      2      0
1      vpp_wk_0            workers     1383    other (0)                6      3      0
2      vpp_wk_1            workers     1384    other (0)                8      4      0
3      vpp_wk_2            workers     1385    other (0)                10     5      0
4      vpp_wk_3            workers     1386    other (0)                12     0      1
```

### 1.4.4. VPP show commands

```
vpp# show dpdk version
DPDK Version:             DPDK 24.03.0
DPDK EAL init args:       --in-memory --no-telemetry --file-prefix vpp -a 0000:07:00.0 -a 0000:08:00.0

vpp# show dpdk buffer
name="vpp pool 0"  available =   15601 allocated =    1183 total =   16784
name="vpp pool 1"  available =   16784 allocated =       0 total =   16784

vpp# show dpdk physmem
Segment 4-0: IOVA:0x113400000, len:2097152, virt:0x7f8e7fe00000, socket_id:0, hugepage_sz:2097152, nchannel:0, nrank:0 fd:16
Segment 4-1: IOVA:0x113600000, len:2097152, virt:0x7f8e80000000, socket_id:0, hugepage_sz:2097152, nchannel:0, nrank:0 fd:19
Segment 4-2: IOVA:0x113800000, len:2097152, virt:0x7f8e80200000, socket_id:0, hugepage_sz:2097152, nchannel:0, nrank:0 fd:22
Segment 8-0: IOVA:0x88e600000, len:2097152, virt:0x7f7e7f600000, socket_id:1, hugepage_sz:2097152, nchannel:0, nrank:0 fd:23
vpp#
```

```
vpp# show interface
              Name               Idx    State  MTU (L3/IP4/IP6/MPLS)     Counter          Count
GigabitEthernet7/0/0              1      up          9000/0/0/0     rx packets                 10864
                                                                    rx bytes                  758310
                                                                    tx packets                     6
                                                                    tx bytes                     252
                                                                    drops                        752
                                                                    punt                           1
                                                                    ip4                        10106
                                                                    ip6                           26
GigabitEthernet8/0/0              2      up          9000/0/0/0     rx packets                   727
                                                                    rx bytes                   38240
                                                                    tx packets                 10112
                                                                    tx bytes                  718740
                                                                    drops                        722
                                                                    ip4                            4
                                                                    ip6                            3
local0                            0     down          0/0/0/0

vpp# show interface  rx-placement
Thread 0 (vpp_main):
 node dpdk-input:
    GigabitEthernet7/0/0 queue 0 (polling)
    GigabitEthernet7/0/0 queue 1 (polling)
    GigabitEthernet8/0/0 queue 0 (polling)
    GigabitEthernet8/0/0 queue 1 (polling)
vpp#
```

```
# vppctl show hardware-interfaces | head -10
              Name                Idx   Link  Hardware
GigabitEthernet7/0/0               1     up   GigabitEthernet7/0/0
  Link speed: unknown
  RX Queues:
    queue thread         mode
    0     main (0)       polling
    1     main (0)       polling
  TX Queues:
    TX Hash: [name: hash-eth-l34 priority: 50 description: Hash ethernet L34 headers]
    queue shared thread(s)
```