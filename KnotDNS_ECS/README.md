# How to configure ECS with Knot DNS

- [How to configure ECS with Knot DNS](#how-to-configure-ecs-with-knot-dns)
  - [Description](#description)
  - [Reference](#reference)
  - [Install and configure ECS](#install-and-configure-ecs)
  - [Confirmation](#confirmation)


## Description

Here is how to configure ECS(EDNS Client Subnet) with Knot DNS.

## Reference

- https://www.knot-dns.cz/docs/3.3/singlehtml/index.html#geoip-geography-based-responses
- https://en.blog.nic.cz/2018/10/16/geoip-in-knot-dns-2-7/

## Install and configure ECS

```
# cat /etc/centos-release ;uname -ri
CentOS Stream release 9
5.14.0-452.el9.x86_64 x86_64
```

Instal knot and geoip module.
```
dnf install -y epel-release
```
```
dnf install -y knot knot-modules-geoip
```

Create a direcotry for zone files
```
mkdir /var/lib/knot/zones
```

You can find configuration files within this direcotry.
```
cp knot.conf /etc/knot/
```

```
cp example.com.zone /var/lib/knot/zones
```

```
cp net.conf /etc/knot/
```

```
chown knot:knot /etc/knot/*.conf
```

```
systemctl start knot.service
```

```
# knotc zone-status example.com
[example.com.] role: master | serial: 2010111213
```

## Confirmation

```
# cat /etc/knot/net.conf
www.example.com:
- net: 192.0.2.0/24
  A: 192.0.2.50
- net: 198.51.100.0/24
  A: 198.51.100.50
- net: 20.0.0.0/8
  A: 1.2.3.4
```

No ECS:
```
# dig @127.1 +short www.example.com a
203.0.113.50
```

With ECS:
```
# dig @127.1 +short www.example.com a +subnet=192.0.2.10
192.0.2.50

# dig @127.1 +short www.example.com a +subnet=30.0.0.0/24
203.0.113.50

# dig @127.1 +short www.example.com a +subnet=192.0.2.10/8
203.0.113.50

# dig @127.1 +short www.example.com a +subnet=192.0.2.10/24
192.0.2.50

# dig @127.1 +short www.example.com a +subnet=30.0.0.0/8
203.0.113.50

# dig @127.1 +short www.example.com a +subnet=20.0.0.0/16
1.2.3.4
```
