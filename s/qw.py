import base64
import requests
import yaml

# Configuration
org = "votre_organisation"
pat = "votre_pat_token"
api_version = "7.1-preview.1"
auth_header = {
    "Authorization": "Basic " + base64.b64encode(f":{pat}".encode()).decode(),
    "Content-Type": "application/json"
}
base_url = f"https://dev.azure.com/{org}"

# 1. Récupérer la liste des projets
def get_projects():
    url = f"{base_url}/_apis/projects?api-version=6.0"
    resp = requests.get(url, headers=auth_header)
    return [proj["name"] for proj in resp.json()["value"]]

# 2. Récupérer les dépôts pour un projet donné
def get_repos(project):
    url = f"{base_url}/{project}/_apis/git/repositories?api-version=6.0"
    resp = requests.get(url, headers=auth_header)
    return resp.json()["value"]

# 3. Récupérer les fichiers YAML dans un dépôt (racine seulement pour démo)
def get_yaml_files(project, repo_id):
    url = f"{base_url}/{project}/_apis/git/repositories/{repo_id}/items?recursionLevel=Full&api-version=6.0"
    resp = requests.get(url, headers=auth_header)
    return [item["path"] for item in resp.json()["value"] if item["path"].endswith(".yml")]

# 4. Télécharger le contenu et chercher IAASPIPELINE
def file_contains_keyword(project, repo_id, path, keyword):
    url = f"{base_url}/{project}/_apis/git/repositories/{repo_id}/items?path={path}&api-version=6.0&includeContent=true"
    resp = requests.get(url, headers=auth_header)
    content = resp.text
    return keyword in content

# Execution
matched_projects = []
for proj in get_projects():
    for repo in get_repos(proj):
        repo_id = repo["id"]
        for yml_path in get_yaml_files(proj, repo_id):
            if file_contains_keyword(proj, repo_id, yml_path, "IAASPIPELINE"):
                matched_projects.append((proj, repo["name"], yml_path))

# Affichage
for match in matched_projects:
    print(f"Projet: {match[0]} | Dépôt: {match[1]} | Fichier: {match[2]}")
