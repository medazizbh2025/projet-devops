# Commandes Docker pour le Projet DevOps

## Construction des Images

### User Service
```bash
# Construire l'image du service utilisateur
cd user-service
docker build -t user-service:latest .

# Construire l'image de la base de données utilisateur
cd db
docker build -t user-db:latest .
```

### Salle Service
```bash
# Construire l'image du service des salles
cd salle-service
docker build -t salle-service:latest .

# Construire l'image de la base de données des salles
cd db
docker build -t salle-db:latest .
```

### Reservation Service
```bash
# Construire l'image du service de réservation
cd reservation-service
docker build -t reservation-service:latest .

# Construire l'image de la base de données de réservation
cd db
docker build -t reservation-db:latest .
```

### SonarQube
```bash
# Construire l'image SonarQube personnalisée
cd sonarqube
docker build -t custom-sonarqube:latest .
```

## Gestion des Containers

### Démarrage des Services
```bash
# Démarrer tous les services
docker-compose up -d

# Démarrer un service spécifique
docker-compose up -d user-service
docker-compose up -d salle-service
docker-compose up -d reservation-service
docker-compose up -d sonarqube
```

### Arrêt des Services
```bash
# Arrêter tous les services
docker-compose down

# Arrêter un service spécifique
docker-compose stop user-service
docker-compose stop salle-service
docker-compose stop reservation-service
```

### Logs et Debugging
```bash
# Voir les logs de tous les services
docker-compose logs

# Voir les logs d'un service spécifique
docker-compose logs user-service
docker-compose logs salle-service
docker-compose logs reservation-service

# Suivre les logs en temps réel
docker-compose logs -f

# Voir les containers en cours d'exécution
docker ps

# Voir tous les containers (même arrêtés)
docker ps -a
```

### Gestion des Images
```bash
# Lister toutes les images
docker images

# Supprimer une image
docker rmi user-service:latest
docker rmi salle-service:latest
docker rmi reservation-service:latest

# Nettoyer toutes les images non utilisées
docker image prune -a
```

### Gestion des Volumes
```bash
# Lister les volumes
docker volume ls

# Supprimer les volumes non utilisés
docker volume prune

# Supprimer un volume spécifique
docker volume rm user-data
docker volume rm salle-data
docker volume rm reservation-data
```

### Maintenance
```bash
# Redémarrer un service
docker-compose restart user-service
docker-compose restart salle-service
docker-compose restart reservation-service

# Reconstruire et redémarrer un service
docker-compose up -d --build user-service
docker-compose up -d --build salle-service
docker-compose up -d --build reservation-service

# Nettoyer le système Docker
docker system prune -a
```

### Commandes de Réseau
```bash
# Lister les réseaux Docker
docker network ls

# Inspecter un réseau
docker network inspect app-network

# Créer un nouveau réseau
docker network create app-network
```

## Commandes pour le Développement

### Tests des Services
```bash
# Exécuter les tests pour un service
docker-compose run --rm user-service python -m pytest
docker-compose run --rm salle-service python -m pytest
docker-compose run --rm reservation-service python -m pytest
```

### Shell dans les Containers
```bash
# Accéder au shell d'un service
docker-compose exec user-service /bin/bash
docker-compose exec salle-service /bin/bash
docker-compose exec reservation-service /bin/bash

# Accéder au shell des bases de données
docker-compose exec user-db psql -U postgres user-service
docker-compose exec salle-db psql -U postgres salle-service
docker-compose exec reservation-db psql -U postgres reservation-service
```

## Notes importantes:
- Assurez-vous d'être dans le répertoire racine du projet pour exécuter les commandes docker-compose
- Les images sont taggées avec 'latest' par défaut
- Les volumes persistent même après l'arrêt des containers
- Utilisez `docker-compose down -v` pour supprimer les volumes en même temps que les containers