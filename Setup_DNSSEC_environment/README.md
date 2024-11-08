# Build DNSEC test environment with SEED Lab

- [Build DNSEC test environment with SEED Lab](#build-dnsec-test-environment-with-seed-lab)
  - [Description](#description)
  - [Reference](#reference)
  - [Walkthrough logs](#walkthrough-logs)
    - [Build and run the containers](#build-and-run-the-containers)
    - [Set up DNSSEC for example.edu domain](#set-up-dnssec-for-exampleedu-domain)
      - [Generate keys](#generate-keys)
      - [Sign the example.edu](#sign-the-exampleedu)
    - [Set up the edu server](#set-up-the-edu-server)
      - [Add the DS record](#add-the-ds-record)
    - [Set up the root server](#set-up-the-root-server)
    - [Set up the local server(full resolver)](#set-up-the-local-serverfull-resolver)

## Description

Here is how to set up a DNSSEC test environment in a containerized environment with SEED Labs. You can evaluate DNSSEC-related tests, such as KSK rollover, with this environment.

## Reference

- https://github.com/seed-labs/seed-labs/tree/master
- [PDF : DNS Security Extensions (DNSSEC) Lab](https://seedsecuritylabs.org/Labs_20.04/Files/DNSSEC/DNSSEC.pdf)

## Walkthrough logs

### Build and run the containers

```
$ cat /etc/fedora-release
Fedora release 41 (Forty One)

$ podman -v
podman version 5.2.5
```

Clone the repo and change the directory.
```
cd seed-labs/category-network/DNSSEC/Labsetup/
```

Pull the base image and add the tag.
```
$ sudo podman image pull docker.io/handsonsecurity/seed-server:bind

$ sudo podman image tag docker.io/handsonsecurity/seed-server:bind seed-base-image-bind:latest
```

Build the images and run the containers.
```
$ sudo podman compose -f docker-compose.yml build

$ sudo podman compose -f docker-compose.yml up -d
```

Confirm all containers are up and running.
```
$ sudo podman compose -f docker-compose.yml ps
>>>> Executing external compose provider "/usr/libexec/docker/cli-plugins/docker-compose". Please see podman-compose(1) for how to disable this message. <<<<

WARN[0000] /home/hattori/Git_works/seed-labs/category-network/DNSSEC/Labsetup/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion
NAME                    IMAGE                                         COMMAND                  SERVICE              CREATED         STATUS         PORTS
edu-10.9.0.60           docker.io/library/edu-server:latest           "/bin/sh -c service …"   edu_server           8 seconds ago   Up 7 seconds

example-edu-10.9.0.65   docker.io/library/example-edu-server:latest   "/bin/sh -c service …"   example_edu_server   9 seconds ago   Up 7 seconds

local-dns-10.9.0.53     docker.io/library/local-dns-server:latest     "/bin/sh -c service …"   local_dns_server     9 seconds ago   Up 7 seconds

root-10.9.0.30          docker.io/library/root-server:latest          "/bin/sh -c service …"   root_server          9 seconds ago   Up 7 seconds

spare-edu-10.9.0.66     docker.io/library/spare-nameserver:latest     "/bin/sh -c service …"   spare_nameserver     9 seconds ago   Up 7 seconds

user-10.9.0.5           docker.io/library/seed-user:latest            "/start.sh"              user                 8 seconds ago   Up 7 seconds
```

### Set up DNSSEC for example.edu domain

#### Generate keys

```
$ cd nameserver/edu.example/
```

Generate ZSK
```
$ dnssec-keygen -a RSASHA256 -b 1024 example.edu
```

Generate KSK
```
$ dnssec-keygen -a RSASHA256 -b 2048 -f KSK example.edu
```

```
$ ls
example.edu.db
Kexample.edu.+008+05868.key
Kexample.edu.+008+05868.private
Kexample.edu.+008+08312.key
Kexample.edu.+008+08312.private
named.conf.seedlabs
```

#### Sign the example.edu

```
$ dnssec-signzone -e 20501231000000 -S -o example.edu example.edu.db
```

Copy the sined zone file.
```
$ sudo sudo podman cp example.edu.db.signed example-edu-10.9.0.65:/etc/bind
```

Edit the conf file to load the singed zone file.
```
$ sudo podman exec example-edu-10.9.0.65 cat /etc/bind/named.conf.seedlabs
zone "example.edu" {
        type master;
        file "/etc/bind/example.edu.db";
};
```

```
$ sudo podman exec example-edu-10.9.0.65 sed -i s/example.edu.db/example.edu.db.signed/ /etc/bind/named.conf.seedlabs
```

```
$ sudo podman  exec example-edu-10.9.0.65 cat /etc/bind/named.conf.seedlabs
zone "example.edu" {
        type master;
        file "/etc/bind/example.edu.db.signed";
};
```

Restart the container
```
$ sudo podman restart example-edu-10.9.0.65
```

Confirm you can get the DNSSEC related responses.
```
$ dig @10.9.0.65 example.edu DNSKEY +dnssec +noall +answer

$ dig @10.9.0.65 www.example.edu A +dnssec +noall +answer
```

### Set up the edu server

#### Add the DS record

Add the DS record of example.edu in its parent zone, the edu.<br>
You can find the DS record in the `edu.example/dsset-example.edu.`
```
$ cat edu.example/dsset-example.edu. | tee -a edu/edu.db
```

```
$ cd edu/
```

Generate ZSK and KSK for the domian edu.
```
$ dnssec-keygen -a RSASHA256 -b 1024 edu
$ dnssec-keygen -a RSASHA256 -b 2048 -f KSK edu
```

Sign the zone.<br>
Make sure you add the DS record of example.edu before sining the zone.
```
$ dnssec-signzone -e 20501231000000 -S -o edu edu.db
```

Copy the zone file.
```
$ sudo podman cp edu.db.signed edu-10.9.0.60:/etc/bind
```

Edit the conf and restart the container
```
$ sudo podman exec edu-10.9.0.60 sed s/edu.db/edu.db.signed/ /etc/bind/named.conf.seedlabs -i
```

```
$ sudo podman exec edu-10.9.0.60 grep file /etc/bind/named.conf.seedlabs
        file "/etc/bind/edu.db.signed";
```

```
$ sudo podman restart edu-10.9.0.60
```

Confirm.
```
$ dig @10.9.0.60 edu DNSKEY +dnssec +noall +answer

$ dig @10.9.0.60 example.edu DS +dnssec +noall +answer
```

### Set up the root server

Add the DS record of edu, then sign the zone.

```
$ cat edu/dsset-edu. | tee -a root/root.db
```

```
$ cd root/
```

```
$ dnssec-keygen -a RSASHA256 -b 1024 .
$ dnssec-keygen -a RSASHA256 -b 2048 -f KSK .
```

```
$ dnssec-signzone -e 20501231000000 -S -o . root.db
``` 

```
$ sudo podman cp root.db.signed root-10.9.0.30:/etc/bind/
```

```
$ sudo podman exec root-10.9.0.30 sed s/root.db/root.db.signed/ /etc/bind/named.conf.seedlabs -i
```

```
$ sudo podman restart root-10.9.0.30
```

Confirm.
```
$ dig @10.9.0.30 . DNSKEY +dnssec
$ dig @10.9.0.30 . NS +dnssec
$ dig @10.9.0.30 edu +dnssec
$ dig @10.9.0.30 example.edu +dnssec
```

### Set up the local server(full resolver)

Add DNSKEY of the root server.
You can find the DNSKEY at `nameserver/root/K.+008+ ... key`<br>

local_dns_server/bind.keys
```
trust-anchors {
. initial-key 257 3 8 " <Root’s Key Signing Key> ";
};
```

Enable DNSSEC validation.
```
$ sed -e s/"dnssec-enable.*"/"dnssec-enable yes;"/ -e s/"dnssec-validation.*"/"dnssec-valid
ation auto;"/  local_dns_server/named.conf.options -i
```

```
$ sudo podman cp local_dns_server/bind.keys local-dns-10.9.0.53:/etc/bind
```

```
$ sudo podman cp local_dns_server/named.conf.options local-dns-10.9.0.53:/etc/bind
```

```
$ sudo podman restart local-dns-10.9.0.53
```

Confirm ad bit is on.
```
$ dig @10.9.0.53 www.example.edu +dnssec
                                                                                                                                                                ; <<>> DiG 9.18.30 <<>> @10.9.0.53 www.example.edu +dnssec
; (1 server found)
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 47798
;; flags: qr rd ra ad; QUERY: 1, ANSWER: 2, AUTHORITY: 0, ADDITIONAL: 1
                                                                                                                                                                ;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags: do; udp: 4096
; COOKIE: 92ccd88c293e832f01000000672ddb36cc9fb7bf75cba141 (good)
;; QUESTION SECTION:
;www.example.edu.               IN      A

;; ANSWER SECTION:
www.example.edu.        259200  IN      A       1.2.3.5
www.example.edu.        259200  IN      RRSIG   A 8 3 259200 20501231000000 20241108061611 5868 example.edu. LpyJ2JIcSQjg02ngD/8hzNlflcH2C6DRiBja+P5ngzXGRy1sXaYG3Wmt irwTkFNvHQp86KeTGzNx57a/xcq/6n7dWdKk0l0JN4NXl2TKyY1uaFCC LrNwCI5yOyaCPOpI0q84XJyLw2Vr+/4ysjSNHq0YSZLaiN3ic63eSk/P msg=

;; Query time: 5 msec
;; SERVER: 10.9.0.53#53(10.9.0.53) (UDP)
;; WHEN: Fri Nov 08 18:34:46 JST 2024
;; MSG SIZE  rcvd: 259
```