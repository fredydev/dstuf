#!/usr/bin/env python3
"""
Script de débogage pour diagnostiquer les problèmes de connexion SonarQube.
"""
import requests
import base64
from sonar_qube_service import SonarQubeService, SonarQubeConfig


def debug_connection():
    """Débogue la connexion SonarQube step par step."""
    print("🔧 Script de débogage SonarQube")
    print("=" * 50)
    
    # Demander les paramètres
    url = input("URL SonarQube (ex: https://sonarqube.example.com): ").strip()
    token = input("Token d'authentification: ").strip()
    
    # Nettoyer l'URL
    url = url.rstrip('/')
    
    print(f"\n📋 Configuration:")
    print(f"URL: {url}")
    print(f"Token: {token[:8]}...")
    
    # Test 1: Vérification de l'URL
    print(f"\n🧪 Test 1: Vérification de l'URL de base")
    try:
        response = requests.get(url, timeout=10)
        print(f"✅ URL accessible - Code: {response.status_code}")
    except Exception as e:
        print(f"❌ URL non accessible: {e}")
        return
    
    # Test 2: Test d'authentification basique
    print(f"\n🧪 Test 2: Test d'authentification")
    token_bytes = f"{token}:".encode('utf-8')
    token_b64 = base64.b64encode(token_bytes).decode('utf-8')
    
    headers = {
        'Authorization': f'Basic {token_b64}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    print(f"Headers utilisés: {list(headers.keys())}")
    
    # Test 3: API system/status
    print(f"\n🧪 Test 3: API system/status")
    try:
        response = requests.get(
            f"{url}/api/system/status",
            headers=headers,
            timeout=30
        )
        print(f"Code de réponse: {response.status_code}")
        print(f"Réponse: {response.text[:200]}...")
        
        if response.ok:
            print("✅ API system/status fonctionne")
        else:
            print(f"❌ Erreur API system/status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'appel API: {e}")
    
    # Test 4: API projects/search
    print(f"\n🧪 Test 4: API projects/search")
    try:
        response = requests.get(
            f"{url}/api/projects/search?ps=10",
            headers=headers,
            timeout=30
        )
        print(f"Code de réponse: {response.status_code}")
        print(f"Réponse: {response.text[:200]}...")
        
        if response.ok:
            data = response.json()
            projects_count = len(data.get('components', []))
            print(f"✅ API projects/search fonctionne - {projects_count} projets trouvés")
        else:
            print(f"❌ Erreur API projects/search: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'appel API: {e}")
    
    # Test 5: Test avec le service
    print(f"\n🧪 Test 5: Test avec SonarQubeService")
    try:
        service = SonarQubeService()
        config = SonarQubeConfig(url=url, token=token)
        service.save_config(config)
        
        success, error = service.test_connection()
        if success:
            print("✅ Service de connexion fonctionne")
        else:
            print(f"❌ Erreur service: {error}")
            
    except Exception as e:
        print(f"❌ Erreur service: {e}")
    
    print(f"\n🏁 Fin du débogage")


if __name__ == "__main__":
    debug_connection()
