#!/bin/bash

kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/storage.yaml
kubectl apply -f k8s/prometheus-config.yaml
kubectl apply -f k8s/prometheus.yaml
kubectl apply -f k8s/grafana.yaml
kubectl apply -f k8s/elasticsearch.yaml
kubectl apply -f k8s/kibana.yaml
kubectl apply -f k8s/firewall-deployment.yaml
kubectl apply -f k8s/monitor-deployment.yaml
kubectl apply -f k8s/switch-deployment.yaml
kubectl apply -f k8s/ingress.yaml

kubectl rollout restart deployment firewall -n nfv-system
kubectl rollout restart deployment monitor -n nfv-system
kubectl rollout restart deployment switch -n nfv-system
