# How to solve /var/lib/libvirt/images Permission denied by Apparmor (Ubuntu 24.04)

## Description

After upgrading to Ubuntu 24.04 and trying to launch VMs using Terraform, I encountered a permission error and discovered<br> 
that AppArmor was blocking this action. Here is how to solve this issue.

## Reference

- [Permission denied on libvirt/images folder when try to boot the VM](https://ubuntuforums.org/showthread.php?t=2495269&s=5d17de2d49109dbbd677d757ba48312a)
- [libvirt: apparmor denies reading from /var/lib/libvirt/images](https://github.com/coreos/bugs/issues/2083)

## How to fix

Add the following line and restart the apparmor.
```
$ sudo grep libvirt/images /etc/apparmor.d/abstractions/libvirt-qemu
  /var/lib/libvirt/images/** rwk,
$

$ sudo systemctl restart apparmor.service
```
