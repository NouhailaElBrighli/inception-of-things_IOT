#!/bin/bash


sudo DEBIAN_FRONTEND=noninteractive apt-get update -y

sudo DEBIAN_FRONTEND=noninteractive apt-get install -y net-tools curl vim docker.io

# echo "something" | docker login --username "nouhaila18" --password-stdin

# Add alias for kubectl
echo 'alias k="kubectl"' >> .bashrc

source .bashrc

SERVER_IP="192.168.56.110"

# install k3s
curl -sfL https://get.k3s.io | sh -s - server --write-kubeconfig-mode 644 --node-ip=$SERVER_IP

kubectl apply -f /vagrant/config/app1/deployment-service.yaml

kubectl apply -f /vagrant/config/app2/deployment-service.yaml

kubectl apply -f /vagrant/config/app3/deployment-service.yaml

kubectl apply -f /vagrant/config/ingress.yaml