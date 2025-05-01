#!/bin/bash

# Créer les namespaces
kubectl create namespace app
kubectl create namespace monitoring

# Appliquer les secrets
kubectl apply -f secrets.yaml -n app

# Déployer les bases de données
kubectl apply -f databases.yaml -n app

# Attendre que les bases de données soient prêtes
echo "Attente du démarrage des bases de données..."
kubectl wait --for=condition=ready pod -l app=postgresql -n app --timeout=300s

# Déployer Kafka et Zookeeper
kubectl apply -f kafka.yaml -n app

# Attendre que Kafka soit prêt
echo "Attente du démarrage de Kafka..."
kubectl wait --for=condition=ready pod -l app=kafka -n app --timeout=300s

# Déployer le monitoring
kubectl apply -f monitoring.yaml -n monitoring

# Déployer les services
kubectl apply -f user-service.yaml -n app
kubectl apply -f salle-service.yaml -n app
kubectl apply -f reservation-service.yaml -n app

# Déployer l'ingress
kubectl apply -f ingress.yaml -n app

echo "Déploiement terminé! Vérification des services..."
kubectl get pods -n app
kubectl get pods -n monitoring