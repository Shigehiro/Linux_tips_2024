# DNS performance tool DNS shotgun

- [DNS performance tool DNS shotgun](#dns-performance-tool-dns-shotgun)
  - [Description](#description)
  - [Reference](#reference)
  - [Build shotgun from the source code on Ubuntu 24.04](#build-shotgun-from-the-source-code-on-ubuntu-2404)
  - [Reply a capture file over UDP](#reply-a-capture-file-over-udp)
  - [Send queries from multiple source IP addresses](#send-queries-from-multiple-source-ip-addresses)
  - [Replay a capture file over TCP](#replay-a-capture-file-over-tcp)
  - [Replay a capture file over DoH](#replay-a-capture-file-over-doh)
  - [Replay a capture file over DoT](#replay-a-capture-file-over-dot)

## Description

Here is how to build, use DNS shotgun.
DNS shotgun is a DNS traffic generator by replaying a pcap file and can generate UDP, TCP, DoH and DoT.

## Reference

https://dns-shotgun.readthedocs.io/en/stable/

## Build shotgun from the source code on Ubuntu 24.04

```
# tail -1 /etc/lsb-release ;uname -ri
DISTRIB_DESCRIPTION="Ubuntu 24.04 LTS"
6.8.0-31-generic x86_64
```

Install required packages via apt.
```
apt install -y build-essential cmake gnutls-dev libuv1-dev libnghttp2-dev dnsjit tshark python3-toml python3-jinja2 python3-matplotlib python3-numpy
```
Then, follow the build instructions at `https://dns-shotgun.readthedocs.io/en/stable/installation/`

Or you can build a Docker image. You can find the Dockerfile at `https://github.com/CZ-NIC/shotgun`

## Reply a capture file over UDP

Tested environment:
```
Shotgun box ----- SW ----- DNS server
192.168.111.235            192.168.111.10
```

For reference, see `https://dns-shotgun.readthedocs.io/en/stable/capturing-traffic/`.
Prepeare a capture file.
On the shotgun box:
```
# tcpdump -nn -i enp1s0 dst 192.168.111.10 and dst port 53 -w dns.cap
```

Send DNS queries:
```
# ./send_dig.py
```

Here is the capture data collected with tcpdump.
```
# tshark -nn -r dns.cap
Running as user "root" and group "root". This could be dangerous.
    1   0.000000 192.168.111.235 → 192.168.111.10 DNS 97 Standard query 0xfa4d AAAA www.google.com OPT
    2   0.021473 192.168.111.235 → 192.168.111.10 DNS 94 Standard query 0x2432 A www.scsk.jp OPT
    3   0.042213 192.168.111.235 → 192.168.111.10 DNS 96 Standard query 0x1092 TXT www.cisco.com OPT
    4   0.053670 192.168.111.235 → 192.168.111.10 DNS 90 Standard query 0xb4fa MX scsk.jp OPT
```

Process the capture file into a pellet which is used to replay the traffic with shotgun.
```
# ./shotgun/pcap/extract-clients.lua -r ./dns.cap -O out_dir/
extract-clients.lua notice: processing entire file as one chunk
extract-clients.lua notice: using input PCAP ./dns.cap
extract-clients.lua notice: writing chunk: out_dir//6881e06e.pcap
extract-clients.lua info:     duration_s: inf
extract-clients.lua info:     number of clients: 1
```

```
# ls out_dir/
6881e06e.pcap
```

```
# tshark -n -r out_dir/6881e06e.pcap
Running as user "root" and group "root". This could be dangerous.
    1   0.000000 fd00::6881:e06e:0:0 → ::1          DNS 103 Standard query 0xfa4d AAAA www.google.com OPT
    2   0.021472 fd00::6881:e06e:0:0 → ::1          DNS 100 Standard query 0x2432 A www.scsk.jp OPT
    3   0.042212 fd00::6881:e06e:0:0 → ::1          DNS 102 Standard query 0x1092 TXT www.cisco.com OPT
    4   0.053669 fd00::6881:e06e:0:0 → ::1          DNS 96 Standard query 0xb4fa MX scsk.jp OPT
```

```
# cp shotgun/configs/udp.toml ./
```

```
# cat udp.toml
# Plain DNS over UDP traffic sender.
[traffic]

# DNS-over-UDP clients.
[traffic.UDP]
protocol = "udp"


[charts]

[charts.latency]
type = "latency"

[charts.response-rate]
type = "response-rate"

[charts.response-rate-rcodes]
type = "response-rate"
rcodes-above-pct = 0

[input]
pcap = "/root/out_dir/6881e06e.pcap"
stop_after_s = 60
```

Replay the capture data.
```
# ./shotgun/replay.py -c ./udp.toml -s 192.168.111.10
```

On the server:<br>
Four DNS queries are replayed becase the catpure file contains four DNS queries.
```
# tcpdump -nn -i eth0 udp port 53
tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
listening on eth0, link-type EN10MB (Ethernet), capture size 262144 bytes
08:06:28.739240 IP 192.168.111.235.52952 > 192.168.111.10.53: 9266+ [1au] A? www.scsk.jp. (52)
08:06:28.739249 IP 192.168.111.235.56256 > 192.168.111.10.53: 64077+ [1au] AAAA? www.google.com. (55)
08:06:28.739315 IP 192.168.111.235.59584 > 192.168.111.10.53: 4242+ [1au] TXT? www.cisco.com. (54)
08:06:28.739326 IP 192.168.111.235.35851 > 192.168.111.10.53: 46330+ [1au] MX? scsk.jp. (48)
08:06:28.739564 IP 192.168.111.10.53 > 192.168.111.235.52952: 9266 1/0/1 A 203.216.212.189 (56)
08:06:28.739584 IP 192.168.111.10.53 > 192.168.111.235.56256: 64077 1/0/1 AAAA 2404:6800:4004:825::2004 (71)
08:06:28.739600 IP 192.168.111.10.53 > 192.168.111.235.35851: 46330 2/0/1 MX mx1.hc744-91.ap.iphmx.com. 10, MX mx2.hc744-91.ap.iphmx.com. 10 (97)
08:06:28.739600 IP 192.168.111.10.53 > 192.168.111.235.59584: 4242 4/1/1 CNAME www.cisco.com.akadns.net., CNAME wwwds.cisco.com.edgekey.net., CNAME wwwds.cisco.com.edgekey.net.globalredir.akadns.net., CNAME e2867.dsca.akamaiedge.net. (269)
```

Replay the cap file over IPv6.
```
# ip -6 a s enp1s0|grep inet6
    inet6 2001:db8:1::123/64 scope global
    inet6 fe80::5054:ff:fe90:67d0/64 scope link

# ./shotgun/replay.py -c ./udp.toml -s 2001:db8:1::10
```

```
# tcpdump -nn -i eth0 port 53
tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
listening on eth0, link-type EN10MB (Ethernet), capture size 262144 bytes
09:09:17.333331 IP6 2001:db8:1::123.59748 > 2001:db8:1::10.53: 64077+ [1au] AAAA? www.google.com. (55)
09:09:17.333332 IP6 2001:db8:1::123.39659 > 2001:db8:1::10.53: 4242+ [1au] TXT? www.cisco.com. (54)
09:09:17.333370 IP6 2001:db8:1::123.52701 > 2001:db8:1::10.53: 9266+ [1au] A? www.scsk.jp. (52)
09:09:17.333373 IP6 2001:db8:1::123.44204 > 2001:db8:1::10.53: 46330+ [1au] MX? scsk.jp. (48)
09:09:17.333601 IP6 2001:db8:1::10.53 > 2001:db8:1::123.59748: 64077 1/0/1 AAAA 2404:6800:4004:825::2004 (71)
09:09:17.333601 IP6 2001:db8:1::10.53 > 2001:db8:1::123.39659: 4242 4/1/1 CNAME www.cisco.com.akadns.net., CNAME wwwds.cisco.com.edgekey.net., CNAME wwwds.cisco.com.edgekey.net.globalredir.akadns.net., CNAME e2867.dsca.akamaiedge.net. (269)
09:09:17.333632 IP6 2001:db8:1::10.53 > 2001:db8:1::123.52701: 9266 1/0/1 A 203.216.212.189 (56)
09:09:17.333641 IP6 2001:db8:1::10.53 > 2001:db8:1::123.44204: 46330 2/0/1 MX mx2.hc744-91.ap.iphmx.com. 10, MX mx1.hc744-91.ap.iphmx.com. 10 (97)
```

## Send queries from multiple source IP addresses

Configure secondary addresses on the shotgun box.<br>
On the shotgun machine:
```
# ip -4 a s enp1s0|grep inet |grep 10.2.0 |head -3
    inet 10.2.0.129/24 brd 10.2.0.255 scope global enp1s0
    inet 10.2.0.130/24 brd 10.2.0.255 scope global secondary enp1s0
    inet 10.2.0.131/24 brd 10.2.0.255 scope global secondary enp1s0

# ip -4 a s enp1s0|grep inet |grep 10.2.0 -c
256
```

Configure the static route on the DNS server so that the DNS server can send the response back to the Shotgun machine.<br>
On the DNS server:
```
# ip r g 10.2
10.2.0.0 via 192.168.111.235 dev eth0 src 192.168.111.10
    cache
```

192.168.111.235 is the IP of shotgun machine.<br>

Replay the capture data from multiple source addresses.
```
# ./shotgun/replay.py -c ./udp.toml -s 192.168.111.10 -b 10.2.0.0/24
```

On the DNS server:
```
# tcpdump -nn -i eth0 port 53
tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
listening on eth0, link-type EN10MB (Ethernet), capture size 262144 bytes
08:46:11.283928 IP 10.2.0.74.46168 > 192.168.111.10.53: 64077+ [1au] AAAA? www.google.com. (55)
08:46:11.283962 IP 10.2.0.2.47190 > 192.168.111.10.53: 4242+ [1au] TXT? www.cisco.com. (54)
08:46:11.284007 IP 10.2.0.129.33795 > 192.168.111.10.53: 9266+ [1au] A? www.scsk.jp. (52)
08:46:11.284030 IP 10.2.0.36.60505 > 192.168.111.10.53: 46330+ [1au] MX? scsk.jp. (48)
08:46:11.284260 IP 192.168.111.10.53 > 10.2.0.74.46168: 64077 1/0/1 AAAA 2404:6800:4004:825::2004 (71)
08:46:11.284283 IP 192.168.111.10.53 > 10.2.0.129.33795: 9266 1/0/1 A 203.216.212.189 (56)
08:46:11.284300 IP 192.168.111.10.53 > 10.2.0.2.47190: 4242 4/1/1 CNAME www.cisco.com.akadns.net., CNAME wwwds.cisco.com.edgekey.net., CNAME wwwds.cisco.com.edgekey.net.globalredir.akadns.net., CNAME e2867.dsca.akamaiedge.net. (269)
08:46:11.284315 IP 192.168.111.10.53 > 10.2.0.36.60505: 46330 2/0/1 MX mx2.hc744-91.ap.iphmx.com. 10, MX mx1.hc744-91.ap.iphmx.com. 10 (97)
```

## Replay a capture file over TCP

Prepare a capture file which contains DNS queries over UDP.
```
# tcpdump -nn -r dns02.cap
reading from file dns02.cap, link-type EN10MB (Ethernet), snapshot length 262144
10:14:45.347671 IP 192.168.111.235.43560 > 192.168.111.10.53: 34603+ [1au] AAAA? www.google.com. (55)
10:14:45.373698 IP 192.168.111.235.42346 > 192.168.111.10.53: 34277+ [1au] A? www.scsk.jp. (52)
10:14:45.385754 IP 192.168.111.235.59967 > 192.168.111.10.53: 40297+ [1au] TXT? www.cisco.com. (54)
10:14:45.720560 IP 192.168.111.235.55581 > 192.168.111.10.53: 57255+ [1au] MX? scsk.jp. (48)
10:14:45.741783 IP 192.168.111.235.39741 > 192.168.111.10.53: 22109+ [1au] MX? google.com. (51)
10:14:45.762706 IP 192.168.111.235.45546 > 192.168.111.10.53: 3025+ [1au] A? www.cisco.com. (54)
10:14:45.792151 IP 192.168.111.235.36650 > 192.168.111.10.53: 47616+ [1au] A? www.redhat.com. (55)
10:14:45.827279 IP 192.168.111.235.60026 > 192.168.111.10.53: 50820+ [1au] A? ubuntu.com. (51)
```

```
# ./shotgun/pcap/extract-clients.lua -r ./dns02.cap -O out_dir02/
```

Prepare the toml file for TCP, `tcp.toml`
```
# DNS-over-TCP traffic senders.
[traffic]

# Well behaved DNS-over-TCP clients utilizing idle connection (default).
[traffic.TCP]
protocol = "tcp"
idle_timeout_s = 0
handshake_timeout_s = 1

[input]
pcap = "/root/out_dir02/5c532a36.pcap"
```

Replay the capture file.
```
# ./shotgun/replay.py -c ./tcp.toml -s 192.168.111.10 -b 10.2.0.0/24
```

On the DNS server:<br>
It seemed that Shotgun replayed multiple DNS queries within a single TCP connection.
```
# tshark -nn -i eth0 port 53
Running as user "root" and group "root". This could be dangerous.
Capturing on 'eth0'
  1 0.000000000    10.2.0.27 -> 192.168.111.10 TCP 74 44607 > 53 [SYN] Seq=0 Win=32120 Len=0 MSS=1460 SACK_PERM=1 TSval=2764921876 TSecr=0 WS=128
  2 0.000046287 192.168.111.10 -> 10.2.0.27    TCP 74 53 > 44607 [SYN, ACK] Seq=0 Ack=1 Win=28960 Len=0 MSS=1460 SACK_PERM=1 TSval=111437400 TSecr=2764921876 WS=128
  3 0.000209674    10.2.0.27 -> 192.168.111.10 TCP 66 44607 > 53 [ACK] Seq=1 Ack=1 Win=32128 Len=0 TSval=2764921877 TSecr=111437400
  4 0.000271845    10.2.0.27 -> 192.168.111.10 DNS 123 Standard query 0x872b  AAAA www.google.com
  5 0.000285560 192.168.111.10 -> 10.2.0.27    TCP 66 53 > 44607 [ACK] Seq=1 Ack=58 Win=29056 Len=0 TSval=111437400 TSecr=2764921877
  6 0.000298860    10.2.0.27 -> 192.168.111.10 DNS 176 Standard query 0x9d69  TXT www.cisco.com
  7 0.000302420 192.168.111.10 -> 10.2.0.27    TCP 66 53 > 44607 [ACK] Seq=1 Ack=168 Win=29056 Len=0 TSval=111437400 TSecr=2764921877
  8 0.000306459    10.2.0.27 -> 192.168.111.10 DNS 116 Standard query 0xdfa7  MX scsk.jp
  9 0.000308409 192.168.111.10 -> 10.2.0.27    TCP 66 53 > 44607 [ACK] Seq=1 Ack=218 Win=29056 Len=0 TSval=111437400 TSecr=2764921877
 10 0.000313051    10.2.0.27 -> 192.168.111.10 DNS 119 Standard query 0x565d  MX google.com
 11 0.000314119 192.168.111.10 -> 10.2.0.27    TCP 66 53 > 44607 [ACK] Seq=1 Ack=271 Win=29056 Len=0 TSval=111437400 TSecr=2764921877
 12 0.000317545    10.2.0.27 -> 192.168.111.10 DNS 232 Standard query 0xc684  A ubuntu.com
```

## Replay a capture file over DoH

You can find sample configs for DoH at:
```
# ls shotgun/configs |grep -E 'doh|dot'
doh-get.toml
doh-post.toml
doh.toml
dot.toml
```

You can generate DoH queries like this:
```
# ./shotgun/replay.py -c doh-get.toml -s 192.168.111.10 -b 10.2.0.0/24
```

On the DNS Server:
```
# tshark -nn -i eth0 -Y '(tcp.port == 443)'
Running as user "root" and group "root". This could be dangerous.
Capturing on 'eth0'
  6 4.730019327   10.2.0.138 -> 192.168.111.10 TCP 66 36227 > 443 [FIN, ACK] Seq=1 Ack=1 Win=249 Len=0 TSval=1778221365 TSecr=199677660
  7 4.730106658 192.168.111.10 -> 10.2.0.138   TLSv1.2 90 Application Data
  8 4.730223508   10.2.0.138 -> 192.168.111.10 TCP 54 36227 > 443 [RST] Seq=2 Win=0 Len=0
 12 6.278807212    10.2.0.84 -> 192.168.111.10 TCP 74 41175 > 443 [SYN] Seq=0 Win=32120 Len=0 MSS=1460 SACK_PERM=1 TSval=4209432381 TSecr=0 WS=128
 13 6.278841886 192.168.111.10 -> 10.2.0.84    TCP 74 443 > 41175 [SYN, ACK] Seq=0 Ack=1 Win=28960 Len=0 MSS=1460 SACK_PERM=1 TSval=199685216 TSecr=4209432381 WS=128
 14 6.279047154    10.2.0.84 -> 192.168.111.10 TCP 66 41175 > 443 [ACK] Seq=1 Ack=1 Win=32128 Len=0 TSval=4209432381 TSecr=199685216
 15 6.279362415    10.2.0.84 -> 192.168.111.10 SSL 444 Client Hello
 16 6.279372700 192.168.111.10 -> 10.2.0.84    TCP 66 443 > 41175 [ACK] Seq=1 Ack=379 Win=30080 Len=0 TSval=199685216 TSecr=4209432382
 17 6.280706456 192.168.111.10 -> 10.2.0.84    TLSv1.2 1627 Server Hello, Change Cipher Spec, Application Data, Application Data, Application Data, Application Data
 18 6.280846706    10.2.0.84 -> 192.168.111.10 TCP 66 41175 > 443 [ACK] Seq=379 Ack=1562 Win=31872 Len=0 TSval=4209432383 TSecr=199685218
 19 6.281266732    10.2.0.84 -> 192.168.111.10 TLSv1.2 72 Change Cipher Spec
 20 6.281628263    10.2.0.84 -> 192.168.111.10 TLSv1.2 140 Application Data
 21 6.281670721 192.168.111.10 -> 10.2.0.84    TCP 66 443 > 41175 [ACK] Seq=1562 Ack=459 Win=30080 Len=0 TSval=199685219 TSecr=4209432383
 22 6.281766901    10.2.0.84 -> 192.168.111.10 TLSv1.2 112 Application Data
 23 6.281774333    10.2.0.84 -> 192.168.111.10 TLSv1.2 109 Application Data
```

## Replay a capture file over DoT

```
# ./shotgun/replay.py -c dot.toml -s 192.168.111.10 -b 10.2.0.0/24
```

On the DNS server:
```
# tshark -nn -i eth0 -Y '(tcp.port == 853)'
Running as user "root" and group "root". This could be dangerous.
Capturing on 'eth0'
  2 0.875390441   10.2.0.136 -> 192.168.111.10 TCP 74 40281 > 853 [SYN] Seq=0 Win=32120 Len=0 MSS=1460 SACK_PERM=1 TSval=3343130912 TSecr=0 WS=128
  3 0.875425561 192.168.111.10 -> 10.2.0.136   TCP 74 853 > 40281 [SYN, ACK] Seq=0 Ack=1 Win=28960 Len=0 MSS=1460 SACK_PERM=1 TSval=199883784 TSecr=3343130912 WS=128
  4 0.875639227   10.2.0.136 -> 192.168.111.10 TCP 66 40281 > 853 [ACK] Seq=1 Ack=1 Win=32128 Len=0 TSval=3343130912 TSecr=199883784
  5 0.875811991   10.2.0.136 -> 192.168.111.10 TCP 435 40281 > 853 [PSH, ACK] Seq=1 Ack=1 Win=32128 Len=369 TSval=3343130912 TSecr=199883784
  6 0.875824313 192.168.111.10 -> 10.2.0.136   TCP 66 853 > 40281 [ACK] Seq=1 Ack=370 Win=30080 Len=0 TSval=199883784 TSecr=3343130912
  7 0.877138226 192.168.111.10 -> 10.2.0.136   TCP 1618 853 > 40281 [PSH, ACK] Seq=1 Ack=370 Win=30080 Len=1552 TSval=199883785 TSecr=3343130912
  8 0.877289179   10.2.0.136 -> 192.168.111.10 TCP 66 40281 > 853 [ACK] Seq=370 Ack=1553 Win=31872 Len=0 TSval=3343130914 TSecr=199883785
```