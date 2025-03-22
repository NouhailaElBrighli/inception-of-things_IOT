#!/bin/bash

sudo DEBIAN_FRONTEND=noninteractive apt-get update -y

sudo DEBIAN_FRONTEND=noninteractive apt-get install -y net-tools curl

# add /usr/sbin to the PATH for run the command ifconfig without sudo
echo 'export PATH=$PATH:/usr/sbin' >> .bashrc

source .bashrc

SERVER_IP="192.168.56.110"
AGENT_IP="192.168.56.111"

# Read the token
NODE_TOKEN=$(cat /vagrant/config/node-token)

# Install K3s Agent
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--node-ip=$AGENT_IP" K3S_URL="https://$SERVER_IP:6443" K3S_TOKEN="$NODE_TOKEN" sh -s - agent
