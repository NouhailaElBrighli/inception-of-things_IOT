#!/bin/bash

sudo DEBIAN_FRONTEND=noninteractive apt-get update -y

# install net-tools (for fconfig) and curl (for download k3s)
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y net-tools curl

# add /usr/sbin to the PATH for run the command ifconfig without sudo
echo 'export PATH=$PATH:/usr/sbin'

SERVER_IP="192.168.56.110"

# install k3s
curl -sfL https://get.k3s.io | sh -s - server --write-kubeconfig-mode 644 --node-ip=$SERVER_IP

# get the k3s token
K3S_TOKEN=$(sudo cat /var/lib/rancher/k3s/server/node-token)

# save the k3s token in the file
echo $K3S_TOKEN > /vagrant/node-token