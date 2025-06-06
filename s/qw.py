import os
import base64
from typing import List
from pathlib import Path

# Simule les fonctions que l'utilisateur implémenterait avec Azure CLI
# Ce bloc est un squelette du script Python attendu, mais ne sera pas exécuté ici.

script = """
import subprocess
import json

# Configuration
ORG_URL = "https://dev.azure.com/<ton-organisation>"

def run_az(command: List[str]) -> str:
    result = subprocess.run(["az"] + command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise Exception(f"Erreur: {result.stderr}")
    return result.stdout.strip()

def get_all_projects() -> List[str]:
    output = run_az(["devops", "project", "list", "--org", ORG_URL, "--query", "value[].name", "-o", "tsv"])
    return output.splitlines()

def get_repos(project: str) -> List[str]:
    output = run_az(["repos", "list", "--project", project, "--org", ORG_URL, "--query", "[].name", "-o", "tsv"])
    return output.splitlines()

def get_yaml_files(project: str, repo: str) -> List[str]:
    output = run_az([
        "repos", "list-items",
        "--project", project,
        "--repository", repo,
        "--path", "/",
        "--recursive",
        "--org", ORG_URL,
        "--query", "[?ends_with(path, '.yml') || ends_with(path, '.yaml')].path",
        "-o", "tsv"
    ])
    return output.splitlines()

def search_pipeline_task(project: str, repo: str, file_path: str, keyword: str) -> bool:
    content = run_az([
        "repos", "item", "show",
        "--project", project,
        "--repository", repo,
        "--path", file_path,
        "--org", ORG_URL,
        "--include-content",
        "--query", "content",
        "-o", "tsv"
    ])
    return keyword in content

def main():
    matching_projects = set()
    projects = get_all_projects()

    for project in projects:
        print(f"🔍 Projet: {project}")
        repos = get_repos(project)

        for repo in repos:
            try:
                files = get_yaml_files(project, repo)
                for file in files:
                    if search_pipeline_task(project, repo, file, "IAASPIPELINE"):
                        print(f"✅ {project} / {repo} / {file}")
                        matching_projects.add(project)
                        break
            except Exception as e:
                print(f"⚠️ Erreur dans {project}/{repo}: {e}")

    print("\\n📋 Projets avec IAASPIPELINE:")
    for proj in sorted(matching_projects):
        print(proj)

if __name__ == "__main__":
    main()
"""

# Write script to file so user can access and use it
script_path = "/mnt/data/check_iaaspipeline_usage.py"
with open(script_path, "w") as f:
    f.write(script)

script_path
