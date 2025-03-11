#!/bin/bash

sudo DEBIAN_FRONTEND=noninteractive apt-get update -y

sudo DEBIAN_FRONTEND=noninteractive apt-get install -y net-tools

echo 'export PATH=$PATH:/sbin:/usr/sbin'