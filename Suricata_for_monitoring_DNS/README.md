# Use Suricata for DNS monitoring

- [Use Suricata for DNS monitoring](#use-suricata-for-dns-monitoring)
  - [Description](#description)
  - [Network topology](#network-topology)
  - [Install Suricata](#install-suricata)
  - [EVE json logs](#eve-json-logs)
  - [Suricata Rules for DNS](#suricata-rules-for-dns)

## Description

Here is how to use Suricata for DNS monitoring.

## Network topology

All machines are running as a virtual machine under KVM
```
     Client
       | .10
       |
       | 10.33.33.0.24
       |
       |
       | .254
      VyOS
       | .254
       |
       | 10.33.34.0/24
       |
       |
(0/0/7)| .253          10.33.36.0/24(SPAN)
      VPP .253(0/0/9)---------------- Suricata
(0/0/8)| .253                         .10
       |
       |
       | 10.33.35.0/24
       |
     DNS Server(10.33.35.20, 21)
```

- Cient : 10.33.33.10
- vyos has two subnets, 10.33.33.254 and 10.33.34.254
- vpp has three subnets, 10.33.34.253, 10.33.35.253 and 10.33.36.253. 10.33.36.253 is for SPAN.

## Install Suricata

Reference:
- https://docs.suricata.io/en/suricata-7.0.3/

<br>I have installed the following version.
```
# tail -1 /etc/lsb-release
DISTRIB_DESCRIPTION="Ubuntu 24.04.1 LTS"

# suricata -V
This is Suricata version 7.0.3 RELEASE
```

Eidt /etc/suricata/suricata.yaml to meet your environment.<br>

Update signatures
```
suricata-update
```

List available signatures
```
# suricata-update list-sources
```

```
systemctl restart suricata.service
```

```
# ps aux |grep suricata |grep -v grep
root         928  2.0  3.9 1447772 485172 ?      Ssl  07:16   1:16 /usr/bin/suricata -D --af-packet -c /etc/suricata/suricata.yaml --pidfile /run/suricata.pid
```

## EVE json logs

Generate traffics, in my case DNS traffics, between the client and the server.<br>
Assume you have already configured the SPAN on the VPP.

On the vpp:
```
# grep span /usr/share/vpp/scripts/vpp-config.txt
set interface span GigabitEthernet7/0/0 destination GigabitEthernet9/0/0 both
```

<br>On the Suricata node:<br>
The number of packets captured by kernel
```
# timeout 15 tail -n0 -f /var/log/suricata/eve.json | jq 'select(.event_type=="stats")|.stats.capture.kernel_packets'
151
157
Terminated
```

<br>DNS UDP packets
```
# timeout 30 tail -n0 -f /var/log/suricata/eve.json | jq 'select(.event_type=="stats")|.stats.app_layer.flow.dns_udp'
461
463
465
466
Terminated
```

<br>DNS TCP packets
```
# timeout 15 tail -n0 -f /var/log/suricata/eve.json | jq 'select(.event_type=="stats")|.stats.app_layer.flow.dns_tcp'
55
70
Terminated
```

<br>DNS requests from the client to the server
```
{
  "timestamp": "2024-11-05T08:14:47.695388+0000",
  "flow_id": 2142245013005619,
  "in_iface": "enp7s0",
  "event_type": "dns",
  "src_ip": "10.33.33.10",
  "src_port": 54689,
  "dest_ip": "10.33.35.20",
  "dest_port": 53,
  "proto": "UDP",
  "pkt_src": "wire/pcap",
  "dns": {
    "type": "query",
    "id": 40505,
    "rrname": "www.google.com",
    "rrtype": "A",
    "tx_id": 0,
    "opcode": 0
  }
}
```

<br>DNS responses from the server being sent to the client
```
{
  "timestamp": "2024-11-05T08:14:47.695941+0000",
  "flow_id": 2142245013005619,
  "in_iface": "enp7s0",
  "event_type": "dns",
  "src_ip": "10.33.33.10",
  "src_port": 54689,
  "dest_ip": "10.33.35.20",
  "dest_port": 53,
  "proto": "UDP",
  "pkt_src": "wire/pcap",
  "dns": {
    "version": 2,
    "type": "answer",
    "id": 40505,
    "flags": "8180",
    "qr": true,
    "rd": true,
    "ra": true,
    "opcode": 0,
    "rrname": "www.google.com",
    "rrtype": "A",
    "rcode": "NOERROR",
    "answers": [
      {
        "rrname": "www.google.com",
        "rrtype": "A",
        "ttl": 293,
        "rdata": "142.250.207.36"
      }
    ],
    "grouped": {
      "A": [
        "142.250.207.36"
      ]
    }
  }
}
```

## Suricata Rules for DNS

Reference
- https://docs.suricata.io/en/suricata-7.0.3/rules/payload-keywords.html#bsize
- https://docs.suricata.io/en/suricata-7.0.3/rules/dns-keywords.html#dns-keywords
- https://github.com/seanlinmt/suricata/blob/master/files/rules/emerging-dns.rules
- `/etc/suricata/rules`, `/var/lib/suricata/rules/suricata.rules` can be found at your Suricata node
- https://www.tcpwave.com/suricata/
- https://www.tcpwave.com/WHITE-PAPERS/Suricata-for-Web.html

<br>You could find some rules by googling `suricata rules dns`

Add my rules
```
# grep ^rule-files /etc/suricata/suricata.yaml -A2
rule-files:
  - suricata.rules
  - local.rules
```

Create a file named local.rules, add a rule, then copy that under `/var/lib/suricata/rules`<br>

local.rules
```
# My DNS rules
alert dns $HOME_NET any -> $DNS_SERVERS 53 (msg:"Test01 bad domain"; dns.query; content:"bad.com"; nocase; endswith; sid:55555;)
```

```
# cp local.rules /var/lib/suricata/rules/
```

<br>Edit suricata.yaml to meet your environment
```
# grep HOME_NET /etc/suricata/suricata.yaml |grep -v "#"|head -1
    HOME_NET: "[10.33.33.0/24]"
```

```
# grep DNS_SERVERS /etc/suricata/suricata.yaml |grep -v "#"
    DNS_SERVERS: "[10.33.35.20,10.33.35.21]"
```

Restart the suricata to reflect the config.
```
# systemctl restart suricata.service
```

Update the signature to reflect the local rules.
```
# suricata-update
```

You will see the alerts as below.
```
# tail -n0 -f /var/log/suricata/fast.log
11/05/2024-11:31:38.160436  [**] [1:55555:0] Test01 bad domain [**] [Classification: (null)] [Priority: 3] {UDP} 10.33.33.10:40289 -> 10.33.35.20:53
11/05/2024-11:31:41.206802  [**] [1:55555:0] Test01 bad domain [**] [Classification: (null)] [Priority: 3] {UDP} 10.33.33.10:38039 -> 10.33.35.20:53
```