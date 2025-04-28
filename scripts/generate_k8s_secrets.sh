#!/bin/bash

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please copy .env.example to .env and fill in your values first."
    exit 1
fi

# Source the .env file
set -a
source .env
set +a

# Function to base64 encode a value
encode_base64() {
    echo -n "$1" | base64
}

# Generate base64 encoded values
cat << EOF > k8s-secrets.env
# Database URLs
USER_DB_URL_BASE64=$(encode_base64 "${USER_DB_URL}")
SALLE_DB_URL_BASE64=$(encode_base64 "${SALLE_DB_URL}")
RESERVATION_DB_URL_BASE64=$(encode_base64 "${RESERVATION_DB_URL}")
DB_PASSWORD_BASE64=$(encode_base64 "${DB_PASSWORD}")

# JWT and OAuth
JWT_SECRET_BASE64=$(encode_base64 "${JWT_SECRET}")
GOOGLE_CLIENT_ID_BASE64=$(encode_base64 "${GOOGLE_CLIENT_ID}")
GOOGLE_CLIENT_SECRET_BASE64=$(encode_base64 "${GOOGLE_CLIENT_SECRET}")

# SonarQube
SONAR_DB_PASSWORD_BASE64=$(encode_base64 "${SONAR_DB_PASSWORD}")
SONAR_TOKEN_BASE64=$(encode_base64 "${SONAR_TOKEN}")
EOF

echo "Generated k8s-secrets.env file with base64 encoded values"
echo "Use these values in your k8s/secrets.yaml file"
echo "WARNING: Keep k8s-secrets.env secure and do not commit it to version control!"