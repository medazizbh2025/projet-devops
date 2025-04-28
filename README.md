# Système de Réservation de Salles

## Architecture

Le système est composé de 3 microservices:
- **user-service** : Gestion des utilisateurs et authentification (OAuth + JWT)
- **salle-service** : Gestion des salles
- **reservation-service** : Gestion des réservations

## Prérequis

- Docker et Docker Compose
- Kubernetes (minikube ou cluster)
- Helm
- Python 3.9+
- SonarQube

## Configuration Locale

1. Cloner le repository:
```bash
git clone <repository-url>
cd projet-devops
```

2. Démarrer les services avec Docker Compose:
```bash
docker-compose up -d
```

3. Accéder aux services:
- User Service: http://localhost:5000
- Salle Service: http://localhost:5001
- Reservation Service: http://localhost:5002
- SonarQube: http://localhost:9000

## Environment Setup

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Configure your environment variables in `.env` with your actual values:
   - Set up Google OAuth credentials from Google Cloud Console
   - Generate a secure JWT secret
   - Configure database passwords
   - Base64 encode values for Kubernetes secrets

3. Update the following environment variables in your `.env` file:
- `DB_PASSWORD`: Database password for PostgreSQL services
- `JWT_SECRET`: Secret key for JWT token generation
- `GOOGLE_CLIENT_ID`: Your Google OAuth Client ID
- `GOOGLE_CLIENT_SECRET`: Your Google OAuth Client Secret
- `SONAR_DB_PASSWORD`: Password for SonarQube database

4. For Kubernetes deployment, you'll need to base64 encode these values:
```bash
echo -n "your-secret-here" | base64
```

### Security Notes
- Never commit the `.env` file to the repository
- Keep your secrets secure and rotate them regularly
- In production, use a secure secrets management service
- For local development, the `.env` file is loaded automatically by docker-compose

⚠️ IMPORTANT: Never commit the `.env` file or any files containing real secrets to the repository.

## Déploiement Kubernetes

1. Configuration de l'environnement:
```bash
kubectl create namespace salle-reservation
kubectl config set-context --current --namespace=salle-reservation
```

2. Déploiement avec Helm:
```bash
helm upgrade --install salle-reservation ./helm
```

## Pipeline CI/CD

Le pipeline GitHub Actions comprend:
1. Analyse SonarQube
2. Tests unitaires
3. Build des images Docker
4. Push vers Docker Hub
5. Déploiement Kubernetes avec Helm

## Monitoring et Logs

- Kafka pour la communication événementielle
- Métriques exposées pour Grafana
- Logs centralisés avec AWS CloudWatch

## Sécurité

- Authentication OAuth (Google)
- JWT pour l'autorisation
- RBAC pour le contrôle d'accès

## Qualité du Code

SonarQube est configuré pour analyser:
- Couverture de tests
- Code smells
- Vulnérabilités
- Dette technique

## Variables d'Environnement Requises

Pour GitHub Actions:
```
DOCKER_USERNAME=<dockerhub-username>
DOCKER_PASSWORD=<dockerhub-password>
KUBE_CONFIG=<base64-encoded-kubeconfig>
SONAR_TOKEN=<sonarqube-token>
SONAR_HOST_URL=<sonarqube-url>
```

Pour les services:
```
GOOGLE_CLIENT_ID=<google-oauth-client-id>
GOOGLE_CLIENT_SECRET=<google-oauth-client-secret>
JWT_SECRET=<jwt-secret-key>
```