# Check if .env file exists
if (-not (Test-Path -Path ".env")) {
    Write-Error "Error: .env file not found!"
    Write-Host "Please copy .env.example to .env and fill in your values first."
    exit 1
}

# Function to base64 encode a value
function Convert-ToBase64 {
    param([string]$value)
    return [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($value))
}

# Read the .env file
$envContent = Get-Content .env
$envVars = @{}
foreach ($line in $envContent) {
    if ($line -match '^([^#][^=]+)=(.*)$') {
        $envVars[$Matches[1].Trim()] = $Matches[2]
    }
}

# Generate base64 encoded values
$outputContent = @"
# Database URLs
USER_DB_URL_BASE64=$(Convert-ToBase64 $envVars['USER_DB_URL'])
SALLE_DB_URL_BASE64=$(Convert-ToBase64 $envVars['SALLE_DB_URL'])
RESERVATION_DB_URL_BASE64=$(Convert-ToBase64 $envVars['RESERVATION_DB_URL'])
DB_PASSWORD_BASE64=$(Convert-ToBase64 $envVars['DB_PASSWORD'])

# JWT and OAuth
JWT_SECRET_BASE64=$(Convert-ToBase64 $envVars['JWT_SECRET'])
GOOGLE_CLIENT_ID_BASE64=$(Convert-ToBase64 $envVars['GOOGLE_CLIENT_ID'])
GOOGLE_CLIENT_SECRET_BASE64=$(Convert-ToBase64 $envVars['GOOGLE_CLIENT_SECRET'])

# SonarQube
SONAR_DB_PASSWORD_BASE64=$(Convert-ToBase64 $envVars['SONAR_DB_PASSWORD'])
"@

# Write to k8s-secrets.env file
$outputContent | Out-File -FilePath "k8s-secrets.env" -Encoding utf8

Write-Host "Generated k8s-secrets.env file with base64 encoded values"
Write-Host "Use these values in your k8s/secrets.yaml file"
Write-Host "WARNING: Keep k8s-secrets.env secure and do not commit it to version control!"