"""
Service SonarQube pour extraire les métriques de qualité des projets.
"""
import json
import base64
import requests
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SonarQubeConfig:
    """Configuration pour la connexion SonarQube."""
    url: str
    token: str


@dataclass
class QualityGateCondition:
    """Condition d'une Quality Gate."""
    metric_key: str
    comparator: str
    period_index: Optional[int] = None
    error_threshold: Optional[str] = None
    actual_value: Optional[str] = None
    status: str = 'NONE'


@dataclass
class QualityGate:
    """Quality Gate d'un projet."""
    id: str
    name: str
    status: str
    conditions: List[QualityGateCondition]


@dataclass
class ProjectMeasure:
    """Mesure d'un projet."""
    metric: str
    value: Optional[str]
    component: str


@dataclass
class SonarProject:
    """Projet SonarQube."""
    key: str
    name: str
    qualifier: str
    visibility: str
    last_analysis_date: Optional[str] = None


@dataclass
class QualityMetrics:
    """Métriques de qualité d'un projet."""
    project_key: str
    project_name: str
    quality_gate_status: str
    coverage: Optional[str] = None
    duplicated_lines_density: Optional[str] = None
    maintainability_rating: Optional[str] = None
    reliability_rating: Optional[str] = None
    security_rating: Optional[str] = None
    vulnerabilities: Optional[str] = None
    bugs: Optional[str] = None
    code_smells: Optional[str] = None
    technical_debt: Optional[str] = None
    lines_of_code: Optional[str] = None
    last_analysis_date: Optional[str] = None


class SonarQubeService:
    """Service pour interagir avec l'API SonarQube."""
    
    CONFIG_FILE = 'sonarqube_config.json'
    
    def __init__(self):
        self._config: Optional[SonarQubeConfig] = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Charge la configuration depuis le fichier."""
        try:
            with open(self.CONFIG_FILE, 'r') as f:
                data = json.load(f)
                self._config = SonarQubeConfig(**data)
        except FileNotFoundError:
            self._config = None
    
    def save_config(self, config: SonarQubeConfig) -> None:
        """Sauvegarde la configuration."""
        self._config = config
        with open(self.CONFIG_FILE, 'w') as f:
            json.dump({
                'url': config.url,
                'token': config.token
            }, f, indent=2)
    
    def get_config(self) -> Optional[SonarQubeConfig]:
        """Retourne la configuration actuelle."""
        return self._config
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Génère les headers d'authentification."""
        if not self._config:
            raise ValueError("Configuration non trouvée")
        
        token_bytes = f"{self._config.token}:".encode('utf-8')
        token_b64 = base64.b64encode(token_bytes).decode('utf-8')
        
        return {
            'Authorization': f'Basic {token_b64}',
            'Content-Type': 'application/json'
        }
    
    def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Teste la connexion à SonarQube."""
        if not self._config:
            return False, "Configuration non trouvée"
        
        try:
            response = requests.get(
                f"{self._config.url}/api/system/status",
                headers=self._get_auth_headers(),
                timeout=30
            )
            
            if not response.ok:
                return False, f"HTTP {response.status_code}: {response.reason}"
            
            data = response.json()
            if data.get('status') == 'UP':
                return True, None
            else:
                return False, f"SonarQube status: {data.get('status')}"
                
        except requests.exceptions.RequestException as e:
            return False, f"Erreur de connexion: {str(e)}"
    
    def get_all_projects(self) -> Tuple[bool, Optional[List[SonarProject]], Optional[str]]:
        """Récupère tous les projets SonarQube."""
        if not self._config:
            return False, None, "Configuration non trouvée"
        
        try:
            response = requests.get(
                f"{self._config.url}/api/projects/search?ps=500",
                headers=self._get_auth_headers(),
                timeout=30
            )
            
            if not response.ok:
                return False, None, f"HTTP {response.status_code}: {response.reason}"
            
            data = response.json()
            projects = []
            
            for component in data.get('components', []):
                project = SonarProject(
                    key=component['key'],
                    name=component['name'],
                    qualifier=component['qualifier'],
                    visibility=component['visibility'],
                    last_analysis_date=component.get('lastAnalysisDate')
                )
                projects.append(project)
            
            return True, projects, None
            
        except requests.exceptions.RequestException as e:
            return False, None, f"Erreur lors de la récupération des projets: {str(e)}"
    
    def get_project_quality_gate(self, project_key: str) -> Optional[QualityGate]:
        """Récupère la Quality Gate d'un projet."""
        if not self._config:
            return None
        
        try:
            response = requests.get(
                f"{self._config.url}/api/qualitygates/project_status",
                params={'projectKey': project_key},
                headers=self._get_auth_headers(),
                timeout=30
            )
            
            if not response.ok:
                return None
            
            data = response.json()
            project_status = data.get('projectStatus')
            
            if not project_status:
                return None
            
            conditions = []
            for condition in project_status.get('conditions', []):
                qg_condition = QualityGateCondition(
                    metric_key=condition['metricKey'],
                    comparator=condition['comparator'],
                    period_index=condition.get('periodIndex'),
                    error_threshold=condition.get('errorThreshold'),
                    actual_value=condition.get('actualValue'),
                    status=condition['status']
                )
                conditions.append(qg_condition)
            
            return QualityGate(
                id=project_status.get('id', ''),
                name=project_status.get('name', ''),
                status=project_status['status'],
                conditions=conditions
            )
            
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la récupération de la Quality Gate pour {project_key}: {e}")
            return None
    
    def get_project_measures(self, project_key: str) -> List[ProjectMeasure]:
        """Récupère les mesures d'un projet."""
        if not self._config:
            return []
        
        metrics = [
            'coverage',
            'duplicated_lines_density',
            'maintainability_rating',
            'reliability_rating',
            'security_rating',
            'vulnerabilities',
            'bugs',
            'code_smells',
            'sqale_index',
            'ncloc'
        ]
        
        try:
            response = requests.get(
                f"{self._config.url}/api/measures/component",
                params={
                    'component': project_key,
                    'metricKeys': ','.join(metrics)
                },
                headers=self._get_auth_headers(),
                timeout=30
            )
            
            if not response.ok:
                return []
            
            data = response.json()
            measures = []
            
            for measure in data.get('component', {}).get('measures', []):
                project_measure = ProjectMeasure(
                    metric=measure['metric'],
                    value=measure.get('value'),
                    component=project_key
                )
                measures.append(project_measure)
            
            return measures
            
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la récupération des mesures pour {project_key}: {e}")
            return []
    
    def get_all_projects_quality_metrics(self) -> Tuple[bool, Optional[List[QualityMetrics]], Optional[str]]:
        """Récupère les métriques de qualité de tous les projets."""
        success, projects, error = self.get_all_projects()
        if not success or not projects:
            return success, None, error
        
        quality_metrics = []
        
        for project in projects:
            try:
                quality_gate = self.get_project_quality_gate(project.key)
                measures = self.get_project_measures(project.key)
                
                measure_map = {m.metric: m.value for m in measures}
                
                metrics = QualityMetrics(
                    project_key=project.key,
                    project_name=project.name,
                    quality_gate_status=quality_gate.status if quality_gate else 'NONE',
                    coverage=measure_map.get('coverage'),
                    duplicated_lines_density=measure_map.get('duplicated_lines_density'),
                    maintainability_rating=measure_map.get('maintainability_rating'),
                    reliability_rating=measure_map.get('reliability_rating'),
                    security_rating=measure_map.get('security_rating'),
                    vulnerabilities=measure_map.get('vulnerabilities'),
                    bugs=measure_map.get('bugs'),
                    code_smells=measure_map.get('code_smells'),
                    technical_debt=measure_map.get('sqale_index'),
                    lines_of_code=measure_map.get('ncloc'),
                    last_analysis_date=project.last_analysis_date
                )
                
                quality_metrics.append(metrics)
                
            except Exception as e:
                print(f"Erreur lors du traitement du projet {project.key}: {e}")
                continue
        
        return True, quality_metrics, None
    
    @staticmethod
    def format_technical_debt(minutes: Optional[str]) -> str:
        """Formate la dette technique en jours et heures."""
        if not minutes:
            return 'N/A'
        
        try:
            total_minutes = int(minutes)
            days = total_minutes // (8 * 60)
            hours = (total_minutes % (8 * 60)) // 60
            
            if days > 0:
                return f"{days}j {hours}h"
            else:
                return f"{hours}h"
        except ValueError:
            return 'N/A'
    
    @staticmethod
    def get_rating_label(rating: Optional[str]) -> str:
        """Convertit une note numérique en lettre."""
        if not rating:
            return 'N/A'
        
        ratings = {'1': 'A', '2': 'B', '3': 'C', '4': 'D', '5': 'E'}
        return ratings.get(rating, rating)
