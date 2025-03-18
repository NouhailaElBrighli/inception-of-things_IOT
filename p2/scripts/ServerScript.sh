#!/bin/bash

sudo DEBIAN_FRONTEND=noninteractive apt-get update -y

sudo DEBIAN_FRONTEND=noninteractive apt-get install -y net-tools curl vim docker.io

# authentication to solve usage limit for docker 
echo "something" | docker login --username "nouhaila18" --password-stdin

# add /usr/sbin to the PATH for run the command ifconfig without sudo
echo 'export PATH=$PATH:/usr/sbin' >> .bashrc

source .bashrc

SERVER_IP="192.168.56.110"

# install k3s
curl -sfL https://get.k3s.io | sh -s - server --write-kubeconfig-mode 644 --node-ip=$SERVER_IP

# whereis kubectl /usr/local/bin/kubectl

kubectl apply -f /vagrant/config/app1/deployment-config.yaml