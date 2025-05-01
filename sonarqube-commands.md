# Commandes SonarQube pour le Projet DevOps

## Démarrage de SonarQube

### Configuration Docker
```bash
# Démarrer SonarQube et sa base de données
docker-compose up -d sonarqube sonarqube-db

# Vérifier les logs de démarrage
docker-compose logs -f sonarqube
```

## Configuration de l'Analyse

### Configuration du Projet
```bash
# Configuration locale (sonar-project.properties)
sonar.projectKey=mon-projet-devops
sonar.projectName=Projet DevOps
sonar.sources=.
sonar.exclusions=**/tests/**,**/migrations/**
sonar.python.coverage.reportPaths=coverage.xml
```

### Exécution de l'Analyse
```bash
# Lancer une analyse avec le scanner
sonar-scanner \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.login=votre-token \
  -Dsonar.projectKey=mon-projet-devops

# Analyse avec couverture de code
pytest --cov=. --cov-report=xml
sonar-scanner \
  -Dsonar.python.coverage.reportPaths=coverage.xml
```

## Administration SonarQube

### Gestion des Quality Gates
```bash
# Importer une Quality Gate (via API REST)
curl -X POST -u admin:admin \
  "http://localhost:9000/api/qualitygates/create" \
  -d "name=DevOps-Gate"

# Configurer les conditions (via interface web)
http://localhost:9000/quality_gates
```

### Gestion des Quality Profiles
```bash
# Créer un nouveau profil (via API REST)
curl -X POST -u admin:admin \
  "http://localhost:9000/api/qualityprofiles/create" \
  -d "language=py&name=Python-DevOps"

# Importer des règles
curl -X POST -u admin:admin \
  "http://localhost:9000/api/qualityprofiles/restore" \
  --form backup=@quality-profile.xml
```

## Intégration Continue

### Jenkins Pipeline
```groovy
stage('SonarQube Analysis') {
    steps {
        withSonarQubeEnv('SonarQube') {
            sh 'sonar-scanner'
        }
    }
}
```

### GitHub Actions
```yaml
sonarqube:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v2
    - name: SonarQube Scan
      uses: sonarsource/sonarqube-scan-action@master
      env:
        SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
        SONAR_HOST_URL: ${{ secrets.SONAR_HOST_URL }}
```

## Monitoring et Maintenance

### Vérification de l'État
```bash
# Vérifier l'état de SonarQube
curl -u admin:admin http://localhost:9000/api/system/status

# Vérifier la santé
curl -u admin:admin http://localhost:9000/api/system/health
```

### Maintenance de la Base de Données
```bash
# Purger les anciennes analyses
curl -X POST -u admin:admin \
  "http://localhost:9000/api/projects/bulk_delete" \
  -d "analyzedBefore=2024-01-01"
```

## API REST Utiles

### Projets
```bash
# Lister tous les projets
curl -u admin:admin http://localhost:9000/api/projects/search

# Obtenir les métriques d'un projet
curl -u admin:admin \
  "http://localhost:9000/api/measures/component?component=mon-projet-devops&metricKeys=bugs,vulnerabilities,code_smells"
```

### Utilisateurs et Permissions
```bash
# Créer un nouveau token
curl -X POST -u admin:admin \
  "http://localhost:9000/api/user_tokens/generate" \
  -d "name=CI-Token"

# Gérer les permissions
curl -X POST -u admin:admin \
  "http://localhost:9000/api/permissions/add_user" \
  -d "login=devops-user&permission=scan"
```

## Notes importantes:
- L'interface web de SonarQube est accessible sur http://localhost:9000
- Credentials par défaut : admin/admin (à changer après la première connexion)
- Attendez que SonarQube soit complètement démarré avant d'exécuter des analyses
- Sauvegardez régulièrement la configuration et les Quality Gates
- Configurez des webhooks pour l'intégration avec CI/CD