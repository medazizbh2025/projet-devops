# Projet DevOps - Système de Réservation de Salles

## Architecture

Le projet est composé de trois microservices :
- User Service (Gestion des utilisateurs)
- Salle Service (Gestion des salles)
- Reservation Service (Gestion des réservations)

## Prérequis

- Docker
- Kubernetes (minikube ou cluster)
- kubectl
- helm (optionnel)

## Configuration

1. Copier le fichier `k8s-secrets.env.example` vers `k8s-secrets.env` et remplir les variables :
```bash
DB_PASSWORD=votre_mot_de_passe
JWT_SECRET=votre_secret_jwt
GOOGLE_CLIENT_ID=votre_client_id
GOOGLE_CLIENT_SECRET=votre_client_secret
SONAR_DB_PASSWORD=votre_sonar_password
```

2. Générer les secrets Kubernetes :
```bash
# Sur Linux/Mac
./scripts/generate_k8s_secrets.sh
# Sur Windows
.\scripts\generate_k8s_secrets.ps1
```

## Déploiement

### Avec kubectl

1. Assurez-vous que votre cluster Kubernetes est opérationnel
2. Exécutez le script de déploiement :
```bash
cd k8s
chmod +x deploy.sh
./deploy.sh
```

### Avec Helm (alternative)

```bash
cd helm
helm dependency update
helm install reservation-system .
```

## Accès aux services

- API Gateway : http://localhost/api
- Interface Jaeger : http://localhost:16686
- SonarQube : http://localhost:9000

## Monitoring

Le projet inclut :
- Elasticsearch pour le stockage des logs
- Jaeger pour le traçage distribué
- Prometheus et Grafana (via Helm) pour la supervision

## Services exposés

- `/api/users` - Service utilisateurs
- `/api/salles` - Service de gestion des salles
- `/api/reservations` - Service de réservation