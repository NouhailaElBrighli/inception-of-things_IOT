#!/bin/bash

# doesn't work it shows always warning dpkg-preconfigure: unable to re-open stdin: No such file or directory
# export DEBIAN_FRONTEND=noninteractive


sudo DEBIAN_FRONTEND=noninteractive apt-get update -y

sudo DEBIAN_FRONTEND=noninteractive apt-get install -y net-tools

echo 'export PATH=$PATH:/sbin:/usr/sbin'