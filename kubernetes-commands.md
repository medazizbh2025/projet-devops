# Commandes Kubernetes pour le Projet DevOps

## Configuration Initiale

### Gestion des Secrets
```bash
# Créer les secrets depuis le fichier
kubectl apply -f k8s/secrets.yaml

# Vérifier les secrets
kubectl get secrets
kubectl describe secret app-secrets
```

### Déploiement des Bases de Données
```bash
# Déployer les bases de données
kubectl apply -f k8s/databases.yaml

# Vérifier les déploiements
kubectl get statefulset
kubectl get pvc
```

### Déploiement de Kafka
```bash
# Déployer Kafka et Zookeeper
kubectl apply -f k8s/kafka.yaml

# Vérifier le déploiement
kubectl get pods -l app=kafka
kubectl get pods -l app=zookeeper
```

## Déploiement des Services

### User Service
```bash
# Déployer le service utilisateur
kubectl apply -f k8s/user-service.yaml

# Vérifier le déploiement
kubectl get deployment user-service
kubectl get service user-service
```

### Salle Service
```bash
# Déployer le service des salles
kubectl apply -f k8s/salle-service.yaml

# Vérifier le déploiement
kubectl get deployment salle-service
kubectl get service salle-service
```

### Reservation Service
```bash
# Déployer le service de réservation
kubectl apply -f k8s/reservation-service.yaml

# Vérifier le déploiement
kubectl get deployment reservation-service
kubectl get service reservation-service
```

### Configuration de l'Ingress
```bash
# Déployer l'ingress
kubectl apply -f k8s/ingress.yaml

# Vérifier l'ingress
kubectl get ingress
```

## Commandes de Monitoring

### Logs et Debug
```bash
# Voir les logs d'un pod
kubectl logs <pod-name>
kubectl logs -f <pod-name>

# Décrire un pod
kubectl describe pod <pod-name>

# Exécuter un shell dans un pod
kubectl exec -it <pod-name> -- /bin/bash
```

### Surveillance des Ressources
```bash
# Voir l'utilisation des ressources
kubectl top pods
kubectl top nodes

# Voir les événements
kubectl get events --sort-by=.metadata.creationTimestamp
```

## Gestion des Applications

### Mise à Jour des Applications
```bash
# Mettre à jour une image
kubectl set image deployment/user-service user-service=user-service:v2
kubectl set image deployment/salle-service salle-service=salle-service:v2
kubectl set image deployment/reservation-service reservation-service=reservation-service:v2

# Voir l'historique des déploiements
kubectl rollout history deployment/user-service
```

### Rollback
```bash
# Annuler un déploiement
kubectl rollout undo deployment/user-service
kubectl rollout undo deployment/salle-service
kubectl rollout undo deployment/reservation-service
```

### Scaling
```bash
# Modifier le nombre de réplicas
kubectl scale deployment user-service --replicas=3
kubectl scale deployment salle-service --replicas=3
kubectl scale deployment reservation-service --replicas=3
```

## Helm Commands

### Installation et Mise à Jour
```bash
# Installation avec Helm
helm install mon-app ./helm

# Mise à jour
helm upgrade mon-app ./helm

# Voir l'historique des releases
helm history mon-app

# Rollback d'une release
helm rollback mon-app 1
```

### Debug avec Helm
```bash
# Vérifier les templates
helm template mon-app ./helm

# Voir les valeurs actuelles
helm get values mon-app

# Vérifier le statut
helm status mon-app
```

## Nettoyage

### Suppression des Ressources
```bash
# Supprimer un déploiement
kubectl delete -f k8s/user-service.yaml
kubectl delete -f k8s/salle-service.yaml
kubectl delete -f k8s/reservation-service.yaml

# Supprimer toutes les ressources
kubectl delete -f k8s/

# Supprimer une release Helm
helm uninstall mon-app
```

## Notes importantes:
- Assurez-vous que kubectl est configuré correctement avec votre cluster
- Vérifiez toujours le contexte kubectl actuel avant d'exécuter des commandes
- Utilisez les labels pour faciliter la gestion des ressources
- Faites attention lors de la suppression des ressources - certaines suppressions sont irréversibles