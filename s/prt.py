"""
Service SonarQube pour extraire les métriques de qualité des projets.
"""
import json
import base64
import requests
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
from tqdm import tqdm


@dataclass
class SonarQubeConfig:
    """Configuration pour la connexion SonarQube."""
    url: str
    token: str
    organization: str = ""


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

@dataclass
class ProjectClassificationStatus:
    """Statut de classification d'un projet selon son intégration SonarQube."""
    project_key: str
    project_name: str
    last_analysis_date: Optional[str] = None
    lines_of_code: Optional[int] = None
    coverage: Optional[float] = None
    duplicated_lines_percent: Optional[float] = None
    bugs: Optional[int] = None
    vulnerabilities: Optional[int] = None
    code_smells: Optional[int] = None
    has_recent_analysis: bool = False
    has_metrics: bool = False
    status: str = 'unknown'  # 'active', 'configured_inactive', 'unknown'

@dataclass  
class ProjectClassification:
    """Classification complète des projets selon leur intégration SonarQube."""
    total: int
    active: int
    configured_inactive: int
    active_projects: List[ProjectClassificationStatus]
    configured_inactive_projects: List[ProjectClassificationStatus]


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
                # Assurer la compatibilité avec les anciennes configs
                if 'organization' not in data:
                    data['organization'] = ""
                self._config = SonarQubeConfig(**data)
        except FileNotFoundError:
            self._config = None
    
    def save_config(self, config: SonarQubeConfig) -> None:
        """Sauvegarde la configuration."""
        self._config = config
        with open(self.CONFIG_FILE, 'w') as f:
            json.dump({
                'url': config.url,
                'token': config.token,
                'organization': config.organization
            }, f, indent=2)
    
    def get_config(self) -> Optional[SonarQubeConfig]:
        """Retourne la configuration actuelle."""
        return self._config
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Génère les headers d'authentification."""
        if not self._config:
            raise ValueError("Configuration non trouvée")
        
        # Nettoyer l'URL (enlever le trailing slash)
        self._config.url = self._config.url.rstrip('/')
        
        token_bytes = f"{self._config.token}:".encode('utf-8')
        token_b64 = base64.b64encode(token_bytes).decode('utf-8')
        
        headers = {
            'Authorization': f'Basic {token_b64}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        return headers
    
    def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Teste la connexion à SonarQube."""
        if not self._config:
            return False, "Configuration non trouvée"
        
        try:
            print(f"🔗 Test de connexion vers: {self._config.url}")
            print(f"🔑 Token utilisé: {self._config.token[:8]}...")
            
            response = requests.get(
                f"{self._config.url}/api/system/status",
                headers=self._get_auth_headers(),
                timeout=30
            )
            
            print(f"📡 Code de réponse: {response.status_code}")
            
            if not response.ok:
                error_msg = f"HTTP {response.status_code}: {response.reason}"
                try:
                    error_detail = response.text
                    if error_detail:
                        error_msg += f"\nDétail: {error_detail}"
                except:
                    pass
                return False, error_msg
            
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
            url = f"{self._config.url}/api/projects/search"
            params = {'ps': '500'}
            if self._config.organization:
                params['organization'] = self._config.organization
                
            print(f"🔍 Récupération des projets: {url}")
            print(f"📋 Paramètres: {params}")
            
            response = requests.get(
                url,
                headers=self._get_auth_headers(),
                params=params,
                timeout=30
            )
            
            print(f"📡 Code de réponse projets: {response.status_code}")
            
            if not response.ok:
                error_msg = f"HTTP {response.status_code}: {response.reason}"
                try:
                    error_detail = response.text
                    if error_detail:
                        error_msg += f"\nDétail: {error_detail}"
                        print(f"❌ Erreur détaillée: {error_detail}")
                except:
                    pass
                return False, None, error_msg
            
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
            
            print(f"✅ {len(projects)} projets trouvés")
            return True, projects, None
            
        except requests.exceptions.RequestException as e:
            return False, None, f"Erreur lors de la récupération des projets: {str(e)}"
    
    def get_project_quality_gate(self, project_key: str) -> Optional[QualityGate]:
        """Récupère la Quality Gate d'un projet."""
        if not self._config:
            return None
        
        try:
            params = {'projectKey': project_key}
            if self._config.organization:
                params['organization'] = self._config.organization
                
            response = requests.get(
                f"{self._config.url}/api/qualitygates/project_status",
                params=params,
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
            'sqale_rating',  # Changé de maintainability_rating
            'reliability_rating',
            'security_rating',
            'vulnerabilities',
            'bugs',
            'code_smells',
            'sqale_index',
            'ncloc'
        ]
        
        try:
            params = {
                'component': project_key,
                'metricKeys': ','.join(metrics)
            }
            if self._config.organization:
                params['organization'] = self._config.organization
                
            response = requests.get(
                f"{self._config.url}/api/measures/component",
                params=params,
                headers=self._get_auth_headers(),
                timeout=30
            )
            
            print(f"   📏 Mesures - Code: {response.status_code}")
            
            if not response.ok:
                print(f"   ❌ Erreur mesures: {response.status_code} - {response.text[:200]}")
                return []
            
            data = response.json()
            print(f"   📊 Mesures trouvées: {len(data.get('component', {}).get('measures', []))}")
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
    
    def get_project_quality_metrics_safe(self, project: SonarProject) -> Optional[QualityMetrics]:
        """Récupère les métriques d'un seul projet de manière sécurisée."""
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
                maintainability_rating=measure_map.get('sqale_rating'),
                reliability_rating=measure_map.get('reliability_rating'),
                security_rating=measure_map.get('security_rating'),
                vulnerabilities=measure_map.get('vulnerabilities'),
                bugs=measure_map.get('bugs'),
                code_smells=measure_map.get('code_smells'),
                technical_debt=measure_map.get('sqale_index'),
                lines_of_code=measure_map.get('ncloc'),
                last_analysis_date=project.last_analysis_date
            )
            
            return metrics
            
        except Exception as e:
            print(f"   ❌ Échec {project.name}: {str(e)}")
            return None

    def get_all_projects_quality_metrics(self) -> Tuple[bool, Optional[List[QualityMetrics]], Optional[str]]:
        """Récupère les métriques de qualité de tous les projets avec parallélisation."""
        success, projects, error = self.get_all_projects()
        if not success or not projects:
            return success, None, error
        
        quality_metrics = []
        total_projects = len(projects)
        
        print(f"🚀 Analyse de {total_projects} projets (parallélisée)...")
        
        # Parallélisation avec ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Créer la barre de progression
            with tqdm(total=total_projects, desc="Projets analysés", 
                     bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]') as pbar:
                
                # Soumettre tous les projets
                future_to_project = {
                    executor.submit(self.get_project_quality_metrics_safe, project): project 
                    for project in projects
                }
                
                # Récupérer les résultats au fur et à mesure
                for future in future_to_project:
                    try:
                        metrics = future.result(timeout=60)  # 60s timeout par projet
                        if metrics:
                            quality_metrics.append(metrics)
                            pbar.set_postfix({"Dernière": metrics.project_name[:20] + "..."})
                        pbar.update(1)
                    except Exception as e:
                        project = future_to_project[future]
                        print(f"\n❌ Timeout/erreur {project.name}: {str(e)}")
                        pbar.update(1)
        
        print(f"\n✅ {len(quality_metrics)}/{total_projects} projets analysés avec succès")
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
    
    def classify_projects(self) -> Tuple[bool, Optional[ProjectClassification], Optional[str]]:
        """
        Classifie tous les projets selon leur statut d'intégration SonarQube.
        
        CLASSIFICATION LOGIQUE :
        
        1. PROJETS ACTIFS (status: 'active') :
           - Analyse récente (< 30 jours)
           - ET métriques présentes (lines of code > 0)
           - ET données de qualité disponibles
           → Projets avec pipeline SonarQube fonctionnel
        
        2. PROJETS CONFIGURÉS MAIS INACTIFS (status: 'configured_inactive') :
           - Projet présent dans SonarQube
           - MAIS analyse ancienne (> 30 jours) ou absente
           - OU métriques vides/nulles (pas de code analysé)
           → Projets connectés mais sans gate SonarQube active
        
        UTILISATION POUR ANALYSE :
        - Export CSV : Colonne 'status' permet le filtrage
        - Graphiques : Ratio projets actifs vs configurés
        - Actions : Identifier les projets à réactiver
        
        Returns:
            Tuple[bool, Optional[ProjectClassification], Optional[str]]: 
            (succès, classification, erreur)
        """
        if not self._config:
            return False, None, "Configuration SonarQube non trouvée"
        
        try:
            print("🔍 Récupération de tous les projets...")
            success, projects, error = self.get_all_projects()
            
            if not success or not projects:
                return False, None, error or "Impossible de récupérer les projets"
            
            print(f"📊 Classification de {len(projects)} projets...")
            
            active_projects = []
            configured_inactive_projects = []
            
            # Date limite pour considérer une analyse comme récente (30 jours)
            from datetime import datetime, timedelta
            thirty_days_ago = datetime.now() - timedelta(days=30)
            
            # Classification en parallèle pour optimiser la performance
            def classify_single_project(project):
                """Classifie un projet unique."""
                try:
                    # Récupérer les métriques du projet
                    measures = self.get_project_measures(project.key)
                    
                    # Créer un dictionnaire des mesures
                    measure_map = {m.metric: m.value for m in measures}
                    
                    # Extraire les données
                    lines_of_code = measure_map.get('ncloc')
                    coverage = measure_map.get('coverage')
                    duplicated_lines = measure_map.get('duplicated_lines_density')
                    bugs = measure_map.get('bugs')
                    vulnerabilities = measure_map.get('vulnerabilities')
                    code_smells = measure_map.get('code_smells')
                    
                    # Convertir en types appropriés
                    lines_of_code_int = int(lines_of_code) if lines_of_code and lines_of_code.isdigit() else 0
                    coverage_float = float(coverage) if coverage else None
                    duplicated_lines_float = float(duplicated_lines) if duplicated_lines else None
                    bugs_int = int(bugs) if bugs and bugs.isdigit() else 0
                     vulnerabilities_int = int(vulnerabilities) if vulnerabilities and vulnerabilities.isdigit() else 0
                     code_smells_int = int(code_smells) if code_smells and code_smells.isdigit() else 0
                     
                     # Vérifier si l'analyse est récente
                     has_recent_analysis = False
                     if project.last_analysis_date:
                         try:
                             # Format attendu: "2024-01-15T10:30:45+0000"
                             analysis_date = datetime.fromisoformat(
                                 project.last_analysis_date.replace('Z', '+00:00').replace('+0000', '+00:00')
                             )
                             has_recent_analysis = analysis_date > thirty_days_ago
                         except ValueError:
                             # Si le parsing échoue, considérer comme ancienne
                             has_recent_analysis = False
                     
                     # Vérifier si le projet a des métriques significatives
                     has_metrics = lines_of_code_int > 0
                     
                     # Déterminer le statut
                     if has_recent_analysis and has_metrics:
                         status = 'active'
                     else:
                         status = 'configured_inactive'
                     
                     # Créer l'objet de classification
                     classification_status = ProjectClassificationStatus(
                         project_key=project.key,
                         project_name=project.name,
                         last_analysis_date=project.last_analysis_date,
                         lines_of_code=lines_of_code_int,
                         coverage=coverage_float,
                         duplicated_lines_percent=duplicated_lines_float,
                         bugs=bugs_int,
                         vulnerabilities=vulnerabilities_int,
                         code_smells=code_smells_int,
                         has_recent_analysis=has_recent_analysis,
                         has_metrics=has_metrics,
                         status=status
                     )
                     
                     return classification_status
                     
                 except Exception as e:
                     print(f"   ❌ Erreur lors de l'analyse: {str(e)}")
                     # Retourner un statut inactif par défaut
                     return ProjectClassificationStatus(
                         project_key=project.key,
                         project_name=project.name,
                         status='configured_inactive'
                     )
            
            # Exécution parallèle de la classification
            with ThreadPoolExecutor(max_workers=10) as executor:
                with tqdm(total=len(projects), desc="Classification en cours", 
                         bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]') as pbar:
                    
                    # Soumettre tous les projets
                    future_to_project = {
                        executor.submit(classify_single_project, project): project 
                        for project in projects
                    }
                    
                    # Récupérer les résultats au fur et à mesure
                    for future in future_to_project:
                        try:
                            classification_status = future.result(timeout=60)
                            if classification_status:
                                if classification_status.status == 'active':
                                    active_projects.append(classification_status)
                                    pbar.set_postfix({"Type": "Actif", "Nom": classification_status.project_name[:15] + "..."})
                                else:
                                    configured_inactive_projects.append(classification_status)
                                    pbar.set_postfix({"Type": "Inactif", "Nom": classification_status.project_name[:15] + "..."})
                            pbar.update(1)
                        except Exception as e:
                            project = future_to_project[future]
                            print(f"\n❌ Timeout/erreur classification {project.name}: {str(e)}")
                            # Ajouter dans les inactifs par défaut
                            classification_status = ProjectClassificationStatus(
                                project_key=project.key,
                                project_name=project.name,
                                status='configured_inactive'
                            )
                            configured_inactive_projects.append(classification_status)
                            pbar.update(1)
            
            # Créer la classification finale
            classification = ProjectClassification(
                total=len(projects),
                active=len(active_projects),
                configured_inactive=len(configured_inactive_projects),
                active_projects=active_projects,
                configured_inactive_projects=configured_inactive_projects
            )
            
            print(f"\n📊 Classification terminée:")
            print(f"   Total: {classification.total} projets")
            print(f"   Actifs: {classification.active} projets ({(classification.active/classification.total*100):.1f}%)")
            print(f"   Configurés inactifs: {classification.configured_inactive} projets ({(classification.configured_inactive/classification.total*100):.1f}%)")
            
            return True, classification, None
            
        except Exception as e:
            return False, None, f"Erreur lors de la classification: {str(e)}"
