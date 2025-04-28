FROM sonarqube:9.9-community

# Installation des plugins nécessaires
RUN apt-get update && apt-get install -y wget unzip

# Plugin Python
RUN wget https://github.com/SonarSource/sonar-python/releases/download/3.9.0.10136/sonar-python-plugin-3.9.0.10136.jar -O /opt/sonarqube/extensions/plugins/sonar-python-plugin.jar

# Plugin de Qualité
RUN wget https://github.com/sbaudoin/sonar-yaml/releases/download/v1.7.0/sonar-yaml-plugin-1.7.0.jar -O /opt/sonarqube/extensions/plugins/sonar-yaml-plugin.jar

# Plugin de Sécurité
RUN wget https://github.com/SonarSource/sonar-security/releases/download/9.9.0.43452/sonar-security-plugin-9.9.0.43452.jar -O /opt/sonarqube/extensions/plugins/sonar-security-plugin.jar

# Copier notre profil de qualité personnalisé
COPY quality-profile.xml /opt/sonarqube/conf/quality-profiles/

# Configuration personnalisée de SonarQube
ENV SONAR_WEB_JAVAADDITIONALOPTS="-javaagent:/opt/sonarqube/extensions/plugins/sonarqube-community-branch-plugin.jar"
ENV SONAR_SECURITY_REALM=GITHUB

# Variables d'environnement pour les performances
ENV SONAR_SCANNER_OPTS="-Xmx512m"
ENV SONAR_WEB_JAVAOPTS="-Xmx512m -Xms128m -XX:+HeapDumpOnOutOfMemoryError"

# Exposer le port par défaut
EXPOSE 9000