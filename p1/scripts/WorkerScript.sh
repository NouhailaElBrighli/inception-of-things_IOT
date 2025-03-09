#!/bin/bash

# doesn't work it shows always warning dpkg-preconfigure: unable to re-open stdin: No such file or directory
export DEBIAN_FRONTEND=noninteractive

export PATH=$PATH:/sbin:/usr/sbin

sudo apt-get update -y

sudo apt-get install -y net-tools