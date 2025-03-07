# Error about Cannot assign requested address (socket bind error EADDRNOTAVAIL)

- [Error about Cannot assign requested address (socket bind error EADDRNOTAVAIL)](#error-about-cannot-assign-requested-address-socket-bind-error-eaddrnotavail)
  - [Description](#description)
  - [Reference](#reference)
  - [How to troubleshoot](#how-to-troubleshoot)
    - [Use strace](#use-strace)
    - [Add the IP command in ExecStartPre.](#add-the-ip-command-in-execstartpre)
  - [How to fix this](#how-to-fix-this)


## Description

The Linux system, especially one that has both IPv4 and IPv6, might encounter a situation where a process fails to start due to the error, **"cannot assign requested address,"** when the OS is booting up.
Here is how to troubleshoot and fix this.

## Reference

- [Beware the IPv6 DAD Race Condition](https://www.agwa.name/blog/post/beware_the_ipv6_dad_race_condition)
- [DNS server does not listen on IPv6 after a reboot](https://askubuntu.com/questions/1261187/dns-server-does-not-listen-on-ipv6-after-a-reboot)
- [Services attempt to bind to IPv6 address before it comes up](https://serverfault.com/questions/1145815/services-attempt-to-bind-to-ipv6-address-before-it-comes-up)
- [Chapter 39. Systemd network targets and services](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/configuring_and_managing_networking/systemd-network-targets-and-services_configuring-and-managing-networking)

## How to troubleshoot

Use strace and/or ip command.

### Use strace

Edit a unit file and start the process with strace. You will see the binding error as shown below in the strace.
```
# grep bind strace.txt |grep -i cannot
876   bind(5, {sa_family=AF_INET6, sin6_port=htons(53), sin6_flowinfo=htonl(0), inet_pton(AF_INET6, "fe80::44f9:dfac:2b5e:5dfe", &sin6_addr), sin6_scope_id=if_nametoindex("eth0")}, 28) = -1 EADDRNOTAVAIL (Cannot assign requested address)
```

### Add the IP command in ExecStartPre.

Add `ip a` to see the network state.
```
ExecStartPre=sh -c "/usr/sbin/ip a > /root/ip_a_execstartpre.txt"
```

If you see IPv6 in the ***tentative*** state as shown below, the process might fail to bind the socket.<br>
The process can not bind the socket if IPv6 is in the tentative state.
```
# grep tentative ip_a_execstartpre.txt
    inet6 fe80::44f9:dfac:2b5e:5dfe/64 scope link tentative noprefixroute
```

or

You might see the log as below.
```
# grep eth0 -A10 ip_a_execstartpre.txt
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 52:54:00:52:b4:c3 brd ff:ff:ff:ff:ff:ff
    altname enp0s3
    altname ens3
```

## How to fix this

**In my experience**, 1, 2, and 3 solved the problem, but 4 did not.

1. Add a sleep command in the unit file to delay the process startup.<br>
   - `ExecStartPre=-/bin/sleep 10`
2. Disable IPv6 DAD of physical NICs
     - `echo 0 > /proc/sys/net/ipv6/conf/eth0/accept_dad`
     - or edit sysctl.conf
        ```
        # grep dad /etc/sysctl.d/99-sysctl.conf
        net.ipv6.conf.eth0.accept_dad = 0
        ```

        ```
        net.ipv6.conf.eth0.autoconf = 0
        net.ipv6.conf.eth0.accept_ra = 0
        net.ipv6.conf.eth0.accept_dad = 0
        ```
3. Disable IPv6 addresses if you do not need them
     - `nmcli connection modify managed-default-eth0 ipv6.method disabled`
4. Use network-online.target ( Edit Unit file )
    ```
    [Unit]
    Wants=network-online.target
    After=network-online.target
    ```
