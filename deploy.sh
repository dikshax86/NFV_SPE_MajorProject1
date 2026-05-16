#!/bin/bash

kubectl apply -f k8s/firewall-deployment.yaml
kubectl apply -f k8s/monitor-deployment.yaml
kubectl apply -f k8s/switch-deployment.yaml

kubectl rollout restart deployment firewall -n nfv-system
kubectl rollout restart deployment monitor -n nfv-system
kubectl rollout restart deployment switch -n nfv-system
