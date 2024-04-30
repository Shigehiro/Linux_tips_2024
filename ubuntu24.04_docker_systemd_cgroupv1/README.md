# Run systemd(init) container under Ubuntu 24.04 Docker CE (cgroup v1)

## Description

How to run a systemd(init) container under Ubuntu 24.04 Docker CE.

## Environment

```
$ tail -1 /etc/lsb-release ; uname  -ri
DISTRIB_DESCRIPTION="Ubuntu 24.04 LTS"
6.8.0-31-generic x86_64
```

```
$ dpkg -l |grep docker
ii  docker-buildx-plugin                 0.14.0-1~ubuntu.24.04~noble             amd64        Docker Buildx cli plugin.
ii  docker-ce                            5:26.1.0-1~ubuntu.24.04~noble           amd64        Docker: the open-source application container engine
ii  docker-ce-cli                        5:26.1.0-1~ubuntu.24.04~noble           amd64        Docker CLI: the open-source application container engine
ii  docker-ce-rootless-extras            5:26.1.0-1~ubuntu.24.04~noble           amd64        Rootless support for Docker.
ii  docker-compose-plugin
```

## Kernel parameters

```
# echo 'GRUB_CMDLINE_LINUX=systemd.unified_cgroup_hierarchy=false' > /etc/default/grub.d/cgroup.cfg
# update-grub
# systemctl reboot
```

```
$ cat /proc/cmdline
BOOT_IMAGE=/vmlinuz-6.8.0-31-generic root=/dev/mapper/ubuntu--vg-ubuntu--lv ro systemd.unified_cgroup_hierarchy=false
```

```
$ mount|grep cgroup
tmpfs on /sys/fs/cgroup type tmpfs (ro,nosuid,nodev,noexec,size=4096k,nr_inodes=1024,mode=755,inode64)
cgroup2 on /sys/fs/cgroup/unified type cgroup2 (rw,nosuid,nodev,noexec,relatime,nsdelegate)
cgroup on /sys/fs/cgroup/systemd type cgroup (rw,nosuid,nodev,noexec,relatime,xattr,name=systemd)
cgroup on /sys/fs/cgroup/net_cls,net_prio type cgroup (rw,nosuid,nodev,noexec,relatime,net_cls,net_prio)
cgroup on /sys/fs/cgroup/misc type cgroup (rw,nosuid,nodev,noexec,relatime,misc)
cgroup on /sys/fs/cgroup/hugetlb type cgroup (rw,nosuid,nodev,noexec,relatime,hugetlb)
cgroup on /sys/fs/cgroup/devices type cgroup (rw,nosuid,nodev,noexec,relatime,devices)
cgroup on /sys/fs/cgroup/pids type cgroup (rw,nosuid,nodev,noexec,relatime,pids)
cgroup on /sys/fs/cgroup/cpu,cpuacct type cgroup (rw,nosuid,nodev,noexec,relatime,cpu,cpuacct)
cgroup on /sys/fs/cgroup/memory type cgroup (rw,nosuid,nodev,noexec,relatime,memory)
cgroup on /sys/fs/cgroup/rdma type cgroup (rw,nosuid,nodev,noexec,relatime,rdma)
cgroup on /sys/fs/cgroup/cpuset type cgroup (rw,nosuid,nodev,noexec,relatime,cpuset)
cgroup on /sys/fs/cgroup/freezer type cgroup (rw,nosuid,nodev,noexec,relatime,freezer)
cgroup on /sys/fs/cgroup/blkio type cgroup (rw,nosuid,nodev,noexec,relatime,blkio)
cgroup on /sys/fs/cgroup/perf_event type cgroup (rw,nosuid,nodev,noexec,relatime,perf_event)
```

```
$ docker info |grep cgroup -i
 Cgroup Driver: cgroupfs
 Cgroup Version: 1
```

## CentOS Stream 8 init container

Here is a sample Dockerfile of CentOS Stream 8.
```
FROM quay.io/centos/centos:stream8

RUN (cd /lib/systemd/system/sysinit.target.wants/; for i in *; do [ $i == \
systemd-tmpfiles-setup.service ] || rm -f $i; done); \
rm -f /lib/systemd/system/multi-user.target.wants/*;\
rm -f /etc/systemd/system/*.wants/*;\
rm -f /lib/systemd/system/local-fs.target.wants/*; \
rm -f /lib/systemd/system/sockets.target.wants/*udev*; \
rm -f /lib/systemd/system/sockets.target.wants/*initctl*; \
rm -f /lib/systemd/system/basic.target.wants/*;\
rm -f /lib/systemd/system/anaconda.target.wants/*;

WORKDIR /root
VOLUME [ "/sys/fs/cgroup" ]
CMD ["/sbin/init"]
```

Build the imaeg, then run the container.
```
docker run -d \
--security-opt seccomp=unconfined \
-v /sys/fs/cgroup:/sys/fs/cgroup:rw \
--cgroup-parent=docker.slice \
--tmpfs /tmp --tmpfs /run --tmpfs /run/lock localhost/cent8:z
```

## CentOS Stream 9 init container

Same configuration as the CentOS Stream 8 container.

```
FROM quay.io/centos/centos:stream9

RUN (cd /lib/systemd/system/sysinit.target.wants/; for i in *; do [ $i == \
systemd-tmpfiles-setup.service ] || rm -f $i; done); \
rm -f /lib/systemd/system/multi-user.target.wants/*;\
rm -f /etc/systemd/system/*.wants/*;\
rm -f /lib/systemd/system/local-fs.target.wants/*; \
rm -f /lib/systemd/system/sockets.target.wants/*udev*; \
rm -f /lib/systemd/system/sockets.target.wants/*initctl*; \
rm -f /lib/systemd/system/basic.target.wants/*;\
rm -f /lib/systemd/system/anaconda.target.wants/*;

WORKDIR /root
VOLUME [ "/sys/fs/cgroup" ]
CMD ["/sbin/init"]
```

```
docker run -d \
--security-opt seccomp=unconfined \
-v /sys/fs/cgroup:/sys/fs/cgroup:rw \
--cgroup-parent=docker.slice \
--tmpfs /tmp --tmpfs /run --tmpfs /run/lock localhost/cent9:z
```

## docker-comopse file

```

...

    volumes:
      - /sys/fs/cgroup:/sys/fs/cgroup:rw
    security_opt:
      - seccomp=unconfined
    cgroup_parent: docker.slice
    tmpfs:
      - /run
      - /run/lock
      - /tmp
...

```