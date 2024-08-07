# Analyze a DNS capture data with zeek

## Description

Here is how to analyze a DNS capture data with zeek.

## Reference

- https://docs.zeek.org/en/master/index.html
- https://docs.zeek.org/en/master/logs/dns.html
- https://activecm.github.io/threat-hunting-labs/dns/

## Walkthrough logs

Prepare the DNS capture data.
```
$ ls
dns.pcap

$ tcpdump -nn -r dns.pcap |head -3
reading from file dns.pcap, link-type EN10MB (Ethernet), snapshot length 262144
17:05:11.942743 IP 10.1.0.10.55198 > 10.2.0.10.53: 2010+ A? www.login.microsoftonline.com. (47)
17:05:12.078516 IP 10.2.0.10.53 > 10.1.0.10.55198: 2010 NXDomain 0/1/0 (143)
17:05:12.943123 IP 10.1.0.10.55198 > 10.2.0.10.53: 2011+ A? www.bing.com. (30)
```

Analyze the wire data.
```
$ sudo podman container run --rm -v $(pwd):/zeek/:rw -w /zeek docker.io/zeek/zeek zeek -r ./dns.pcap local Log::default_logdir=/zeek
```

You can see the some log files as below.
```
$ ls *.log
capture_loss.log  conn.log  dns.log  known_services.log  loaded_scripts.log  notice.log  packet_filter.log  stats.log  telemetry.log
```

Here is the dns.log generated by zeek.
```
$ head -15 dns.log 
#separator \x09
#set_separator  ,
#empty_field    (empty)
#unset_field    -
#path   dns
#open   2024-08-07-08-26-21
#fields ts      uid     id.orig_h       id.orig_p       id.resp_h       id.resp_p       proto   trans_id        rtt     query   qclass  qclass_name     qtype   qtype_name      rcode   rcode_name      AA      TC      RD      RA      Z    answers  TTLs    rejected
#types  time    string  addr    port    addr    port    enum    count   interval        string  count   string  count   string  count   string  bool    bool    bool    bool    count   vector[string]  vector[interval]        bool
1723017911.942743       CWf5Ue4OkWfzok4Dth      10.1.0.10       55198   10.2.0.10       53      udp     2010    -       www.login.microsoftonline.com   1       C_INTERNET      1       A       3       NXDOMAIN        F       F       T    F0       -       -       F
1723017912.943123       CWf5Ue4OkWfzok4Dth      10.1.0.10       55198   10.2.0.10       53      udp     2011    0.040320        www.bing.com    1       C_INTERNET      1       A       0       NOERROR F       F       T       T       0    www-www.bing.com.trafficmanager.net,www.bing.com.edgekey.net,e86303.dscx.akamaiedge.net,23.37.92.182,23.37.92.184,23.37.92.179,23.37.92.176,23.37.92.177,23.37.92.185,23.37.92.181,23.37.92.183,23.37.92.178     14056.000000,60.000000,14056.000000,20.000000,20.000000,20.000000,20.000000,20.000000,20.000000,20.000000,20.000000,20.000000 F
1723017913.943140       CWf5Ue4OkWfzok4Dth      10.1.0.10       55198   10.2.0.10       53      udp     2012    -       www.edge.microsoft.com  1       C_INTERNET      1       A       3       NXDOMAIN        F       F       T       F    0-       -       F
1723017914.943036       CWf5Ue4OkWfzok4Dth      10.1.0.10       55198   10.2.0.10       53      udp     2013    -       www.settings-win.data.microsoft.com     1       C_INTERNET      1       A       3       NXDOMAIN        F       F    TF       0       -       -       F
1723017915.942916       CWf5Ue4OkWfzok4Dth      10.1.0.10       55198   10.2.0.10       53      udp     2014    0.297771        www.office.net  1       C_INTERNET      1       A       0       NOERROR F       F       T       T       0    microsoftoffice.com      3600.000000     F
1723017916.942792       CWf5Ue4OkWfzok4Dth      10.1.0.10       55198   10.2.0.10       53      udp     2015    -       www.ecs.office.com      1       C_INTERNET      1       A       3       NXDOMAIN        F       F       T       F    0-       -       F
1723017917.943095       CWf5Ue4OkWfzok4Dth      10.1.0.10       55198   10.2.0.10       53      udp     2016    -       www.update.googleapis.com       1       C_INTERNET      1       A       3       NXDOMAIN        F       F       T    F0       -       -       F
```

With zeek-cut.
```
$ sudo podman container run --rm -v $(pwd):/zeek/:rw -w /zeek docker.io/zeek/zeek sh -c "cat dns.log | zeek-cut id.orig_h query answers" | head -10
10.1.0.10       www.login.microsoftonline.com   -
10.1.0.10       www.bing.com    www-www.bing.com.trafficmanager.net,www.bing.com.edgekey.net,e86303.dscx.akamaiedge.net,23.37.92.182,23.37.92.184,23.37.92.179,23.37.92.176,23.37.92.177,23.37.92.185,23.37.92.181,23.37.92.183,23.37.92.178
10.1.0.10       www.edge.microsoft.com  -
10.1.0.10       www.settings-win.data.microsoft.com     -
10.1.0.10       www.office.net  microsoftoffice.com
10.1.0.10       www.ecs.office.com      -
10.1.0.10       www.update.googleapis.com       -
10.1.0.10       www.mp.microsoft.com    -
10.1.0.10       www.e2ro.com    -
```

More with zeek-cut
```
$ sudo podman container run --rm -v $(pwd):/zeek/:rw -w /zeek docker.io/zeek/zeek sh -c "cat dns.log | zeek-cut id.orig_h qtype_name rcode_name query answers" | head -5
10.1.0.10       A       NXDOMAIN        www.login.microsoftonline.com   -
10.1.0.10       A       NOERROR www.bing.com    www-www.bing.com.trafficmanager.net,www.bing.com.edgekey.net,e86303.dscx.akamaiedge.net,23.37.92.182,23.37.92.184,23.37.92.179,23.37.92.176,23.37.92.177,23.37.92.185,23.37.92.181,23.37.92.183,23.37.92.178
10.1.0.10       A       NXDOMAIN        www.edge.microsoft.com  -
10.1.0.10       A       NXDOMAIN        www.settings-win.data.microsoft.com     -
10.1.0.10       A       NOERROR www.office.net  microsoftoffice.com
```

Dump logs with JSON format
```
sudo podman container run --rm -v $(pwd):/zeek/:rw -w /zeek docker.io/zeek/zeek zeek -r ./dns.pcap local Log::default_logdir=/zeek -C LogAscii::use_json=T
```

```
$ jq . -c dns.log|head -3
{"ts":1723017911.942743,"uid":"CNaPJKtFuB0pPuUrj","id.orig_h":"10.1.0.10","id.orig_p":55198,"id.resp_h":"10.2.0.10","id.resp_p":53,"proto":"udp","trans_id":2010,"query":"www.login.microsoftonline.com","qclass":1,"qclass_name":"C_INTERNET","qtype":1,"qtype_name":"A","rcode":3,"rcode_name":"NXDOMAIN","AA":false,"TC":false,"RD":true,"RA":false,"Z":0,"rejected":false}
{"ts":1723017912.943123,"uid":"CNaPJKtFuB0pPuUrj","id.orig_h":"10.1.0.10","id.orig_p":55198,"id.resp_h":"10.2.0.10","id.resp_p":53,"proto":"udp","trans_id":2011,"rtt":0.04031991958618164,"query":"www.bing.com","qclass":1,"qclass_name":"C_INTERNET","qtype":1,"qtype_name":"A","rcode":0,"rcode_name":"NOERROR","AA":false,"TC":false,"RD":true,"RA":true,"Z":0,"answers":["www-www.bing.com.trafficmanager.net","www.bing.com.edgekey.net","e86303.dscx.akamaiedge.net","23.37.92.182","23.37.92.184","23.37.92.179","23.37.92.176","23.37.92.177","23.37.92.185","23.37.92.181","23.37.92.183","23.37.92.178"],"TTLs":[14056.0,60.0,14056.0,20.0,20.0,20.0,20.0,20.0,20.0,20.0,20.0,20.0],"rejected":false}
{"ts":1723017913.94314,"uid":"CNaPJKtFuB0pPuUrj","id.orig_h":"10.1.0.10","id.orig_p":55198,"id.resp_h":"10.2.0.10","id.resp_p":53,"proto":"udp","trans_id":2012,"query":"www.edge.microsoft.com","qclass":1,"qclass_name":"C_INTERNET","qtype":1,"qtype_name":"A","rcode":3,"rcode_name":"NXDOMAIN","AA":false,"TC":false,"RD":true,"RA":false,"Z":0,"rejected":false}
```