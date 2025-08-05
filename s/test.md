# SonarQube Quality Metrics Extractor - Documentation Complète

## Vue d'ensemble

Ce projet Python permet d'extraire les métriques de qualité de tous les projets SonarQube pour le processus de conformité Nexus, avec classification automatique des projets et tests unitaires complets.

## 🚀 Installation et Configuration

### Prérequis
- Python 3.7+
- Accès à une instance SonarQube
- Token d'authentification SonarQube

### Installation
```bash
pip install -r requirements.txt
```

### Configuration initiale
```bash
python main.py --configure
```

Vous devrez fournir :
- URL de SonarQube (ex: https://sonar.example.com)
- Token d'authentification

## 📊 Utilisation

### Commandes principales

#### Extraction standard des métriques
```bash
python main.py
```

#### Test de connexion
```bash
python main.py --test-connection
```

#### Classification des projets
```bash
# Affichage console
python main.py --classify

# Export CSV
python main.py --classify --export-csv classification_report.csv

# Export JSON
python main.py --classify --export-json classification_report.json
```

#### Exports personnalisés
```bash
# Export CSV avec nom personnalisé
python main.py --export-csv metrics_nexus_2024.csv

# Export JSON avec nom personnalisé
python main.py --export-json metrics_nexus_2024.json
```

### Options complètes
```bash
python main.py --help
```

## 🏗️ Architecture

### Classes principales

- **SonarQubeService** : Service principal pour interagir avec l'API SonarQube
- **SonarQubeConfig** : Configuration de connexion (URL + token)
- **QualityMetrics** : Métriques de qualité d'un projet
- **ProjectClassification** : Classification des projets (Actif/Inactif)
- **SonarProject** : Représentation d'un projet SonarQube
- **QualityGate** : Quality Gate d'un projet

### Structure des fichiers
```
script_python_version/
├── main.py                       # Point d'entrée principal
├── __main__.py                   # Entry point pour module
├── sonar_qube_service.py         # Service SonarQube
├── requirements.txt              # Dépendances
├── pytest.ini                   # Configuration tests
├── run_tests.py                  # Script de test
├── test_sonar_qube_service.py    # Tests du service
├── test_main.py                  # Tests du main
└── README_*.md                   # Documentation
```

## 📈 Métriques Extraites

### Métriques de qualité
- Quality Gate Status (Passé/Échec/Avertissement)
- Couverture de code
- Densité de duplication
- Notes de maintenabilité, fiabilité, sécurité (A-E)
- Nombre de vulnérabilités, bugs, code smells
- Dette technique (en jours/heures)
- Lignes de code
- Date de dernière analyse

### Classification des projets

#### Projets Actifs
- Analyse récente (< 90 jours)
- Métriques présentes (lignes de code > 0)
- Quality Gate fonctionnel

#### Projets Configurés mais Inactifs
- Pas d'analyse récente (> 90 jours)
- Métriques vides
- Quality Gate inactif

## 📁 Formats d'Export

### CSV
- Format séparé par point-virgule (;)
- Encodage UTF-8
- Nom par défaut : `nexus_quality_metrics_YYYYMMDD_HHMMSS.csv`

### JSON
- Format JSON avec indentation
- Nom par défaut : `nexus_quality_metrics_YYYYMMDD_HHMMSS.json`

### Export de classification
- Statistiques de distribution
- Liste des projets par catégorie
- Recommandations d'actions

## 🧪 Tests

### Structure des tests
```
script_python_version/
├── test_sonar_qube_service.py    # Tests pour SonarQubeService
├── test_main.py                  # Tests pour main.py
├── run_tests.py                  # Script pour lancer les tests
├── pytest.ini                   # Configuration pytest
└── requirements.txt              # Dépendances (incluant pytest-cov)
```

### Lancer les tests

#### Option 1: Script automatique
```bash
python run_tests.py
```

#### Option 2: Pytest direct
```bash
cd script_python_version
python -m pytest test_*.py --cov=. --cov-report=html --cov-report=term-missing --cov-fail-under=80 -v
```

#### Option 3: Module consensus
```bash
python -m pytest consensus/script_python_version/test_*.py --cov=consensus/script_python_version --cov-report=html -v
```

### Couverture des tests (Objectif: 80%+)

#### SonarQubeService
- ✅ Configuration (save/load)
- ✅ Authentification
- ✅ Test de connexion (succès/échec)
- ✅ Récupération des projets
- ✅ Quality gates
- ✅ Métriques des projets
- ✅ Classification des projets
- ✅ Formatage des données
- ✅ Gestion des erreurs

#### Main
- ✅ Fonctions d'export (CSV/JSON)
- ✅ Export de classification
- ✅ Arguments CLI (--classify, --export-*)
- ✅ Gestion des erreurs de configuration
- ✅ Gestion des erreurs de connexion
- ✅ Comportement par défaut

## 📊 Analyse et Workflows

### Workflow recommandé

1. **Audit Initial**
   ```bash
   python main.py --classify --export-csv audit_initial.csv
   ```

2. **Analyse des données**
   - Utiliser Excel/PowerBI pour analyser le CSV
   - Identifier les projets critiques
   - Planifier les actions correctives

3. **Actions correctives**
   - Réactiver les projets inactifs importants
   - Nettoyer les projets obsolètes
   - Former les équipes

4. **Surveillance périodique**
   ```bash
   python main.py --classify --export-csv monitoring_mensuel.csv
   ```

### Métriques de succès

#### KPIs recommandés
- **Adoption SonarQube** : % projets actifs > 80%
- **Quality Gates** : % projets PASSED > 85%
- **Couverture** : % projets avec couverture > 70%
- **Dette technique** : Moyenne < 2 jours/projet

### Intégration CI/CD

#### Script mensuel automatique
```bash
#!/bin/bash
# Rapport mensuel SonarQube
DATE=$(date +%Y%m%d)
python main.py --classify --export-csv "rapport_sonarqube_$DATE.csv"
python main.py --export-csv "metriques_sonarqube_$DATE.csv"

# Analyse automatique
python -c "
import csv
with open('rapport_sonarqube_$DATE.csv', 'r') as f:
    reader = csv.DictReader(f, delimiter=';')
    projects = list(reader)
    active = len([p for p in projects if p['Statut'] == 'Actif'])
    total = len(projects)
    print(f'Adoption SonarQube: {active}/{total} ({active/total*100:.1f}%)')
"
```

## 🔧 Gestion des Erreurs

- Timeout des requêtes HTTP (30 secondes)
- Gestion des erreurs réseau
- Validation de la connexion SonarQube
- Logs d'erreur pour les projets problématiques
- Configuration persistante dans `sonarqube_config.json`

## 💡 Exemples Avancés

### Analyse personnalisée
```python
from sonar_qube_service import SonarQubeService

service = SonarQubeService()
success, metrics, error = service.get_all_projects_quality_metrics()

if success:
    # Projets avec faible couverture
    low_coverage = [m for m in metrics if m.coverage and float(m.coverage) < 80]
    
    # Projets avec beaucoup de dette technique
    high_debt = [m for m in metrics if m.technical_debt and int(m.technical_debt) > 1440]  # > 3 jours
    
    print(f"Projets avec couverture < 80%: {len(low_coverage)}")
    print(f"Projets avec dette > 3j: {len(high_debt)}")
```

### Script d'intégration continue
```bash
#!/bin/bash
# Vérifier la connexion
python main.py --test-connection || exit 1

# Extraire les métriques
python main.py --export-csv "nexus_$(date +%Y%m%d).csv"

# Analyser les résultats
python -c "
import csv
with open('nexus_$(date +%Y%m%d).csv', 'r') as f:
    reader = csv.DictReader(f, delimiter=';')
    failed = [row for row in reader if row['Quality Gate'] == 'ERROR']
    if failed:
        print(f'❌ {len(failed)} projets en échec')
        exit(1)
    else:
        print('✅ Tous les projets conformes')
"
```

## 📚 Documentation Additionnelle

- **README.md** : Documentation principale
- **README_TESTS.md** : Documentation complète des tests
- **README_CLASSIFICATION.md** : Guide détaillé de classification
- **README_GLOBAL.md** : Cette documentation (vue d'ensemble)

## 🛠️ Dépendances

### Production
- `requests>=2.28.0` - Requêtes HTTP
- `dataclasses` - Classes de données (Python < 3.7)

### Tests
- `pytest>=7.0.0` - Framework de test
- `pytest-cov>=4.1.0` - Plugin de couverture
- `coverage>=7.2.0` - Outil de mesure de couverture

## 📞 Support

Pour toute question ou problème :
1. Vérifier la configuration SonarQube
2. Tester la connexion : `python main.py --test-connection`
3. Consulter les logs d'erreur
4. Vérifier les permissions du token SonarQube
