import requests
import json

# Paramètres de connexion Azure DevOps
organization_url = 'https://dev.azure.com/{organization_name}'  # Remplace par ton organisation AzDO
project_name = '{project_name}'  # Remplace par le nom de ton projet AzDO
personal_access_token = '{your_pat_token}'  # Remplace par ton Personal Access Token

# URL pour créer la connexion de service dans Azure DevOps
service_connection_url = f'{organization_url}/{project_name}/_apis/serviceendpoint/endpoints?api-version=7.1-preview.4'

# Headers d'authentification
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Basic {personal_access_token}'
}

# Données minimales pour créer la connexion SnapLogic (sans info d'authentification)
service_connection_data = {
    "type": "generic",  # Type de connexion (tu peux aussi spécifier un autre type comme REST)
    "name": "SnapLogic Service Connection",  # Nom de la connexion
    "description": "Service connection for SnapLogic integration"
}

# Effectuer la requête POST pour créer la connexion de service
response = requests.post(service_connection_url, headers=headers, data=json.dumps(service_connection_data))

# Vérifier la réponse
if response.status_code == 201:
    print("Connexion de service SnapLogic créée avec succès.")
    print(response.json())
else:
    print(f"Erreur lors de la création de la connexion de service: {response.status_code}")
    print(response.text)
