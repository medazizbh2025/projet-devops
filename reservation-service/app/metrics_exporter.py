from prometheus_client import Gauge
import os
import requests
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Define Prometheus metrics
sonarqube_coverage = Gauge('sonarqube_coverage', 'Code coverage percentage', ['project'])
sonarqube_bugs = Gauge('sonarqube_bugs', 'Number of bugs', ['project', 'severity'])
sonarqube_vulnerabilities = Gauge('sonarqube_vulnerabilities', 'Number of vulnerabilities', ['project', 'severity'])
sonarqube_code_smells = Gauge('sonarqube_code_smells', 'Number of code smells', ['project'])
sonarqube_technical_debt = Gauge('sonarqube_technical_debt_minutes', 'Technical debt in minutes', ['project'])
sonarqube_duplicated_lines = Gauge('sonarqube_duplicated_lines_density', 'Percentage of duplicated lines', ['project'])
sonarqube_quality_gate = Gauge('sonarqube_quality_gate_status', 'Quality gate status (0=failed, 1=passed)', ['project'])

def fetch_sonarqube_metrics():
    """Fetch metrics from SonarQube and update Prometheus gauges"""
    sonar_url = os.getenv('SONARQUBE_URL', 'http://sonarqube:9000')
    sonar_token = os.getenv('SONAR_TOKEN')
    project_key = 'salle-reservation'

    if not sonar_token:
        logger.error('SONAR_TOKEN not configured')
        return

    headers = {'Authorization': f'Bearer {sonar_token}'}

    try:
        # Fetch main metrics
        metrics_response = requests.get(
            f'{sonar_url}/api/measures/component',
            headers=headers,
            params={
                'component': project_key,
                'metricKeys': 'coverage,bugs,vulnerabilities,code_smells,'
                            'sqale_index,duplicated_lines_density'
            }
        )
        metrics_response.raise_for_status()
        metrics_data = metrics_response.json()

        # Fetch issues for severity breakdown
        issues_response = requests.get(
            f'{sonar_url}/api/issues/search',
            headers=headers,
            params={
                'componentKeys': project_key,
                'types': 'BUG,VULNERABILITY',
                'facets': 'severities'
            }
        )
        issues_response.raise_for_status()
        issues_data = issues_response.json()

        # Fetch quality gate status
        gate_response = requests.get(
            f'{sonar_url}/api/qualitygates/project_status',
            headers=headers,
            params={'projectKey': project_key}
        )
        gate_response.raise_for_status()
        gate_data = gate_response.json()

        # Update metrics
        for measure in metrics_data['component']['measures']:
            if measure['metric'] == 'coverage':
                sonarqube_coverage.labels(project=project_key).set(float(measure['value']))
            elif measure['metric'] == 'code_smells':
                sonarqube_code_smells.labels(project=project_key).set(int(measure['value']))
            elif measure['metric'] == 'sqale_index':
                sonarqube_technical_debt.labels(project=project_key).set(int(measure['value']))
            elif measure['metric'] == 'duplicated_lines_density':
                sonarqube_duplicated_lines.labels(project=project_key).set(float(measure['value']))

        # Update issues by severity
        severity_counts = {
            'bugs': {'BLOCKER': 0, 'CRITICAL': 0, 'MAJOR': 0, 'MINOR': 0, 'INFO': 0},
            'vulnerabilities': {'BLOCKER': 0, 'CRITICAL': 0, 'MAJOR': 0, 'MINOR': 0, 'INFO': 0}
        }

        for facet in issues_data.get('facets', []):
            if facet['property'] == 'severities':
                for value in facet['values']:
                    severity = value['val']
                    count = value['count']
                    if 'bug' in value.get('label', '').lower():
                        severity_counts['bugs'][severity] = count
                    elif 'vulnerability' in value.get('label', '').lower():
                        severity_counts['vulnerabilities'][severity] = count

        for severity, count in severity_counts['bugs'].items():
            sonarqube_bugs.labels(project=project_key, severity=severity.lower()).set(count)

        for severity, count in severity_counts['vulnerabilities'].items():
            sonarqube_vulnerabilities.labels(project=project_key, severity=severity.lower()).set(count)

        # Update quality gate status
        quality_gate_status = 1 if gate_data['projectStatus']['status'] == 'OK' else 0
        sonarqube_quality_gate.labels(project=project_key).set(quality_gate_status)

        logger.info(f'Successfully updated SonarQube metrics for project {project_key}')

    except requests.exceptions.RequestException as e:
        logger.error(f'Error fetching SonarQube metrics: {str(e)}')
    except (KeyError, ValueError) as e:
        logger.error(f'Error parsing SonarQube response: {str(e)}')