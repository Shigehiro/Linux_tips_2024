# Play with Polar DNS

## Reference

- https://github.com/oryxlabs/PolarDNS

## Run Polar DNS

Clone the repository and run the script.
```
# cat /etc/fedora-release ;python --version
Fedora release 40 (Forty)
Python 3.12.4
```

RUn the script.
```
# python3 polardns.py 
1724253104.5379500 | PolarDNS v1.4 server starting up
1724253104.5386410 | Starting listener at tcp://0.0.0.0:53
1724253104.5391588 | Starting listener at udp://0.0.0.0:53
1724253123.7617629 | udp://localhost:36501 1791 A always.yourdomain.com | A 2.3.4.5
1724253127.6166650 | udp://localhost:45165 5a70 A always.tc.yourdomain.com | only a header with truncated flag (TC)
1724253127.6174433 | tcp://localhost:36693 d1ac A always.tc.yourdomain.com | A 2.3.4.5
1724253141.4946783 | udp://localhost:36605 6914 A always.ttl2000000000.slp1500.yourdomain.com | A 2.3.4.5
1724253161.4705644 | udp://localhost:58626 b491 A size.512.yourdomain.com | 29 A records in 512 B packet size limit
1724253209.8112130 | udp://192.168.103.10:60394 b4be A size.512.yourdomain.com | 29 A records in 512 B packet size limit
```

Send queries from the remote node.

Large resopnse.
```
# dig @192.168.103.20 size.1000.yourdomain.com |grep 'MSG SIZE' 
;; MSG SIZE  rcvd: 986
```

Force truncate.
```
# dig @192.168.103.20 always.tc.yourdomain.com | head -1
;; Truncated, retrying in TCP mode.
```

Add latency before returing the answer.
```
# dig @192.168.103.20 always.slp500.yourdomain.com |grep 'Query time'
;; Query time: 503 msec
```

```
# dig @192.168.103.20 TXT whatismyip.yourdomain.com +noall +answer
whatismyip.yourdomain.com. 60   IN      TXT     "192.168.103.10:50208"
```