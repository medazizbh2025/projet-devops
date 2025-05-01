# Commandes pour Docker, Kubernetes et SonarQube

## Docker Commands

### Démarrage des services Docker
```bash
# Construire et démarrer tous les services
docker-compose up -d

# Construire sans cache
docker-compose build --no-cache

# Arrêter tous les services
docker-compose down

# Voir les logs
docker-compose logs -f

# Vérifier l'état des services
docker-compose ps
```

## Kubernetes Commands

### Configuration initiale
```bash
# Créer les secrets Kubernetes
kubectl create -f k8s/secrets.yaml

# Appliquer les configurations de base de données
kubectl apply -f k8s/databases.yaml

# Déployer Kafka
kubectl apply -f k8s/kafka.yaml

# Déployer les microservices
kubectl apply -f k8s/user-service.yaml
kubectl apply -f k8s/salle-service.yaml
kubectl apply -f k8s/reservation-service.yaml

# Déployer l'ingress
kubectl apply -f k8s/ingress.yaml
```

### Commandes de gestion Kubernetes
```bash
# Vérifier l'état des pods
kubectl get pods

# Vérifier les services
kubectl get services

# Vérifier les déploiements
kubectl get deployments

# Voir les logs d'un pod
kubectl logs <pod-name>

# Supprimer tous les ressources
kubectl delete -f k8s/
```

### Helm Commands (pour le déploiement complet)
```bash
# Installer avec Helm
helm install mon-app ./helm

# Mettre à jour le déploiement
helm upgrade mon-app ./helm

# Supprimer le déploiement
helm uninstall mon-app
```

## SonarQube Commands

### Configuration SonarQube
```bash
# Démarrer SonarQube (si utilisation standalone)
docker-compose up -d sonarqube sonarqube-db

# Attendre que SonarQube soit prêt (environ 2-3 minutes)
# Accéder à SonarQube: http://localhost:9000
# Credentials par défaut: admin/admin

# Lancer une analyse
sonar-scanner \
  -Dsonar.projectKey=mon-projet \
  -Dsonar.sources=. \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.login=votre-token
```

## Commandes de Monitoring

### Elasticsearch & Jaeger
```bash
# Vérifier Elasticsearch
curl http://localhost:9200/_cluster/health

# Accéder à Jaeger UI
# http://localhost:16686
```

## Commandes de Nettoyage
```bash
# Nettoyer Docker
docker-compose down -v
docker system prune -a

# Nettoyer Kubernetes
kubectl delete namespace mon-namespace
helm uninstall mon-app
```

## Notes importantes
- Assurez-vous que Docker Desktop est en cours d'exécution avant d'exécuter les commandes
- Attendez que chaque service soit complètement démarré avant de passer au suivant
- Vérifiez les logs en cas d'erreur
- Sauvegardez vos données avant le nettoyage