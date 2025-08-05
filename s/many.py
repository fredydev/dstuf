def print_stats(metrics):
    """Affiche les statistiques des métriques."""
    total = len(metrics)
    passed = len([m for m in metrics if m.quality_gate_status == 'OK'])
    failed = len([m for m in metrics if m.quality_gate_status == 'ERROR'])
    warned = len([m for m in metrics if m.quality_gate_status == 'WARN'])
    
    print(f"\n📊 Statistiques Nexus:")
    print(f"Total des projets: {total}")
    print(f"✅ Passés: {passed}")
    print(f"❌ Échecs: {failed}")
    print(f"⚠️  Avertissements: {warned}")
    print(f"📈 Taux de réussite: {(passed/total*100):.1f}%" if total > 0 else "N/A")


def export_to_csv(metrics, filename=None):
    """Exporte les métriques vers un fichier CSV."""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"nexus_quality_metrics_{timestamp}.csv"
    
    headers = [
        'Projet', 'Clé', 'Quality Gate', 'Couverture', 'Duplication',
        'Maintenabilité', 'Fiabilité', 'Sécurité', 'Vulnérabilités',
        'Bugs', 'Code Smells', 'Dette technique', 'Lignes de code',
        'Dernière analyse'
    ]
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(headers)
        
        for metric in metrics:
            row = [
                metric.project_name,
                metric.project_key,
                metric.quality_gate_status,
                metric.coverage or '',
                metric.duplicated_lines_density or '',
                SonarQubeService.get_rating_label(metric.maintainability_rating),
                SonarQubeService.get_rating_label(metric.reliability_rating),
                SonarQubeService.get_rating_label(metric.security_rating),
                metric.vulnerabilities or '',
                metric.bugs or '',
                metric.code_smells or '',
                SonarQubeService.format_technical_debt(metric.technical_debt),
                metric.lines_of_code or '',
                metric.last_analysis_date or ''
            ]
            writer.writerow(row)
    
    print(f"📄 Export CSV sauvegardé: {filename}")


def export_to_json(metrics, filename=None):
    """Exporte les métriques vers un fichier JSON."""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"nexus_quality_metrics_{timestamp}.json"
    
    # Conversion en dictionnaire pour la sérialisation JSON
    metrics_dict = []
    for metric in metrics:
        metric_dict = {
            'projectKey': metric.project_key,
            'projectName': metric.project_name,
            'qualityGateStatus': metric.quality_gate_status,
            'coverage': metric.coverage,
            'duplicatedLinesDensity': metric.duplicated_lines_density,
            'maintainabilityRating': metric.maintainability_rating,
            'reliabilityRating': metric.reliability_rating,
            'securityRating': metric.security_rating,
            'vulnerabilities': metric.vulnerabilities,
            'bugs': metric.bugs,
            'codeSmells': metric.code_smells,
            'technicalDebt': metric.technical_debt,
            'linesOfCode': metric.lines_of_code,
            'lastAnalysisDate': metric.last_analysis_date
        }
        metrics_dict.append(metric_dict)
    
    with open(filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(metrics_dict, jsonfile, indent=2, ensure_ascii=False)
    
    print(f"📄 Export JSON sauvegardé: {filename}")


def export_classification_to_csv(classification: ProjectClassification, filename: str = None) -> None:
    """
    Exporte la classification des projets au format CSV.
    
    Args:
        classification: Classification des projets à exporter
        filename: Nom du fichier de sortie (optionnel)
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sonarqube_classification_{timestamp}.csv"
    
    # Combiner tous les projets
    all_projects = classification.active_projects + classification.configured_inactive_projects
    
    headers = [
        'Projet', 'Clé', 'Statut', 'Dernière Analyse', 'Lignes de Code',
        'Couverture (%)', 'Duplication (%)', 'Bugs', 'Vulnérabilités', 
        'Code Smells', 'Analyse Récente', 'A des Métriques'
    ]
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            
            for project in all_projects:
                # Formatter la date
                last_analysis = 'Jamais'
                if project.last_analysis_date:
                    try:
                        date_obj = datetime.fromisoformat(
                            project.last_analysis_date.replace('Z', '+00:00').replace('+0000', '+00:00')
                        )
                        last_analysis = date_obj.strftime("%Y-%m-%d")
                    except ValueError:
                        last_analysis = project.last_analysis_date
                
                # Déterminer le statut en français
                status_fr = 'Actif' if project.status == 'active' else 'Configuré mais Inactif'
                
                row = [
                    project.project_name,
                    project.project_key,
                    status_fr,
                    last_analysis,
                    project.lines_of_code or 0,
                    f"{project.coverage:.1f}" if project.coverage is not None else 'N/A',
                    f"{project.duplicated_lines_percent:.1f}" if project.duplicated_lines_percent is not None else 'N/A',
                    project.bugs or 0,
                    project.vulnerabilities or 0,
                    project.code_smells or 0,
                    'Oui' if project.has_recent_analysis else 'Non',
                    'Oui' if project.has_metrics else 'Non'
                ]
                writer.writerow(row)
        
        print(f"📄 Classification exportée vers: {filename}")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'export CSV de la classification: {e}")

def export_classification_to_json(classification: ProjectClassification, filename: str = None) -> None:
    """
    Exporte la classification des projets au format JSON.
    
    Args:
        classification: Classification des projets à exporter
        filename: Nom du fichier de sortie (optionnel)
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sonarqube_classification_{timestamp}.json"
    
    try:
        # Convertir en dictionnaire pour la sérialisation JSON
        data = {
            'metadata': {
                'export_date': datetime.now().isoformat(),
                'total_projects': classification.total,
                'active_projects': classification.active,
                'configured_inactive_projects': classification.configured_inactive,
                'active_percentage': round((classification.active / classification.total) * 100, 1) if classification.total > 0 else 0
            },
            'active_projects': [
                {
                    'project_key': p.project_key,
                    'project_name': p.project_name,
                    'last_analysis_date': p.last_analysis_date,
                    'lines_of_code': p.lines_of_code,
                    'coverage': p.coverage,
                    'duplicated_lines_percent': p.duplicated_lines_percent,
                    'bugs': p.bugs,
                    'vulnerabilities': p.vulnerabilities,
                    'code_smells': p.code_smells,
                    'has_recent_analysis': p.has_recent_analysis,
                    'has_metrics': p.has_metrics,
                    'status': p.status
                }
                for p in classification.active_projects
            ],
            'configured_inactive_projects': [
                {
                    'project_key': p.project_key,
                    'project_name': p.project_name,
                    'last_analysis_date': p.last_analysis_date,
                    'lines_of_code': p.lines_of_code,
                    'coverage': p.coverage,
                    'duplicated_lines_percent': p.duplicated_lines_percent,
                    'bugs': p.bugs,
                    'vulnerabilities': p.vulnerabilities,
                    'code_smells': p.code_smells,
                    'has_recent_analysis': p.has_recent_analysis,
                    'has_metrics': p.has_metrics,
                    'status': p.status
                }
                for p in classification.configured_inactive_projects
            ]
        }
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=2, ensure_ascii=False)
        
        print(f"📄 Classification exportée vers: {filename}")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'export JSON de la classification: {e}")

def print_classification_stats(classification: ProjectClassification) -> None:
    """
    Affiche les statistiques de classification des projets.
    
    Args:
        classification: Classification des projets
    """
    print("\n" + "="*60)
    print("📊 STATISTIQUES DE CLASSIFICATION DES PROJETS")
    print("="*60)
    
    total = classification.total
    active = classification.active
    inactive = classification.configured_inactive
    
    print(f"📁 Total des projets SonarQube: {total}")
    print(f"✅ Projets actifs (gate SonarQube fonctionnelle): {active}")
    print(f"⚠️  Projets configurés mais inactifs: {inactive}")
    
    if total > 0:
        active_pct = (active / total) * 100
        inactive_pct = (inactive / total) * 100
        
        print(f"\n📈 Répartition:")
        print(f"   Actifs: {active_pct:.1f}%")
        print(f"   Inactifs: {inactive_pct:.1f}%")
        
        print(f"\n💡 Recommandations:")
        if active_pct < 50:
            print("   🔴 Taux d'adoption faible - Considérer une campagne d'activation")
        elif active_pct < 80:
            print("   🟡 Taux d'adoption moyen - Identifier les projets à réactiver")
        else:
            print("   🟢 Excellent taux d'adoption SonarQube!")
    
    print("="*60)

def configure_sonar():
    """Configure la connexion SonarQube."""
    print("🔧 Configuration SonarQube")
    url = input("URL SonarQube: ").strip()
    token = input("Token d'authentification: ").strip()
    
    service = SonarQubeService()
    config = SonarQubeConfig(url=url, token=token)
    service.save_config(config)
    
    # Test de la connexion
    success, error = service.test_connection()
    if success:
        print("✅ Connexion réussie!")
        return service
    else:
        print(f"❌ Échec de la connexion: {error}")
        return None


def main():
    """Fonction principale du script."""
    parser = argparse.ArgumentParser(
        description='Extracteur de métriques de qualité SonarQube',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:

  # Configuration initiale
  python main.py --configure

  # Test de connexion
  python main.py --test-connection

  # Extraction des métriques de qualité (mode classique)
  python main.py --export-csv metrics.csv --export-json metrics.json

  # Classification des projets (nouveau)
  python main.py --classify --export-classification-csv classification.csv

  # Classification avec export JSON
  python main.py --classify --export-classification-json classification.json

  # Classification complète avec tous les exports
  python main.py --classify --export-classification-csv --export-classification-json

CLASSIFICATION DES PROJETS:
  La fonctionnalité de classification distingue:
  
  • PROJETS ACTIFS: Analyse récente (< 30 jours) + métriques présentes
    → Projets avec pipeline SonarQube fonctionnel
    
  • PROJETS CONFIGURÉS INACTIFS: Analyse ancienne ou métriques vides
    → Projets connectés mais sans gate SonarQube active
    
  Utilisez cette classification pour identifier les projets à réactiver
  et mesurer le taux d'adoption SonarQube dans votre organisation.
        """
    )
    
    parser.add_argument('--configure', action='store_true', help='Configure la connexion SonarQube')
    parser.add_argument('--test-connection', action='store_true', help='Teste la connexion SonarQube')
    parser.add_argument('--export-csv', nargs='?', const=True, help='Export CSV des métriques (fichier optionnel)')
    parser.add_argument('--export-json', nargs='?', const=True, help='Export JSON des métriques (fichier optionnel)')
    
    # Nouveaux arguments pour la classification
    parser.add_argument('--classify', action='store_true', help='Classification des projets selon leur intégration SonarQube')
    parser.add_argument('--export-classification-csv', nargs='?', const=True, help='Export CSV de la classification (fichier optionnel)')
    parser.add_argument('--export-classification-json', nargs='?', const=True, help='Export JSON de la classification (fichier optionnel)')
    
    args = parser.parse_args()
    
    service = SonarQubeService()
    
    # Configuration
    if args.configure:
        service = configure_sonar()
        if not service:
            return 1
    
    # Vérification de la configuration
    if not service.get_config():
        print("❌ Aucune configuration trouvée. Utilisez --configure pour configurer SonarQube.")
        return 1
    
    # Test de connexion
    if args.test_connection:
        success, error = service.test_connection()
        if success:
            print("✅ Connexion SonarQube réussie!")
        else:
            print(f"❌ Échec de la connexion: {error}")
        return 0 if success else 1
    
    # Mode classification des projets
    if args.classify:
        print("🔍 Classification des projets selon leur intégration SonarQube...")
        success, classification, error = service.classify_projects()
        
        if not success:
            print(f"❌ Erreur lors de la classification: {error}")
            return 1
        
        if not classification:
            print("⚠️  Aucun projet trouvé pour la classification.")
            return 0
        
        # Affichage des statistiques de classification
        print_classification_stats(classification)
        
        # Exports de la classification
        if args.export_classification_csv:
            filename = args.export_classification_csv if isinstance(args.export_classification_csv, str) else None
            export_classification_to_csv(classification, filename)
        
        if args.export_classification_json:
            filename = args.export_classification_json if isinstance(args.export_classification_json, str) else None
            export_classification_to_json(classification, filename)
        
        # Export par défaut si aucun export spécifié
        if not args.export_classification_csv and not args.export_classification_json:
            export_classification_to_csv(classification)
            export_classification_to_json(classification)
        
        print("✅ Classification terminée avec succès!")
        return 0
    
    # Mode classique - Récupération des métriques de qualité
    print("🔍 Récupération des métriques de qualité...")
    success, metrics, error = service.get_all_projects_quality_metrics()
    
    if not success:
        print(f"❌ Erreur: {error}")
        return 1
    
    if not metrics:
        print("⚠️  Aucun projet trouvé.")
        return 0
    
    # Affichage des statistiques
    print_stats(metrics)
    
    # Exports
    if args.export_csv:
        filename = args.export_csv if isinstance(args.export_csv, str) else None
        export_to_csv(metrics, filename)
    
    if args.export_json:
        filename = args.export_json if isinstance(args.export_json, str) else None
        export_to_json(metrics, filename)
    
    # Export par défaut si aucun export spécifié
    if not args.export_csv and not args.export_json:
        export_to_csv(metrics)
        export_to_json(metrics)
    
    print("✅ Extraction terminée avec succès!")
    return 0


if __name__ == "__main__":
    exit(main())
