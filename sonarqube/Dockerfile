FROM sonarqube:9.9-community

USER root
# Installation des plugins nécessaires
RUN apt-get update && apt-get install -y wget unzip

# Plugin Python
RUN wget https://binaries.sonarsource.com/Distribution/sonar-python-plugin/sonar-python-plugin-4.1.0.11333.jar -O /opt/sonarqube/extensions/plugins/sonar-python-plugin.jar

# Plugin de Qualité
RUN wget https://github.com/sbaudoin/sonar-yaml/releases/download/v1.7.0/sonar-yaml-plugin-1.7.0.jar -O /opt/sonarqube/extensions/plugins/sonar-yaml-plugin.jar

# Create quality profiles directory if it doesn't exist
RUN mkdir -p /opt/sonarqube/conf/quality-profiles/

# Copier notre profil de qualité personnalisé
COPY quality-profile.xml /opt/sonarqube/conf/quality-profiles/

# Switch back to sonarqube user for security
USER sonarqube

# Configuration personnalisée de SonarQube
ENV SONAR_WEB_JAVAADDITIONALOPTS="-javaagent:/opt/sonarqube/extensions/plugins/sonarqube-community-branch-plugin.jar"
ENV SONAR_SECURITY_REALM="GITHUB"

# Variables d'environnement pour les performances
ENV SONAR_SCANNER_OPTS="-Xmx512m"
ENV SONAR_WEB_JAVAOPTS="-Xmx512m -Xms128m -XX:+HeapDumpOnOutOfMemoryError"

# Exposer le port par défaut
EXPOSE 9000