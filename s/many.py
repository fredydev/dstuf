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
    """Fonction principale."""
    parser = argparse.ArgumentParser(description="Script d'extraction des métriques de qualité SonarQube")
    parser.add_argument('--configure', action='store_true', help='Configure la connexion SonarQube')
    parser.add_argument('--export-csv', metavar='FILENAME', help='Exporte vers un fichier CSV')
    parser.add_argument('--export-json', metavar='FILENAME', help='Exporte vers un fichier JSON')
    parser.add_argument('--test-connection', action='store_true', help='Teste la connexion SonarQube')
    
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
    
    # Récupération des métriques
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
        export_to_csv(metrics, args.export_csv)
    
    if args.export_json:
        export_to_json(metrics, args.export_json)
    
    # Export par défaut si aucun export spécifié
    if not args.export_csv and not args.export_json:
        export_to_csv(metrics)
        export_to_json(metrics)
    
    print("✅ Extraction terminée avec succès!")
    return 0


if __name__ == "__main__":
    exit(main())
