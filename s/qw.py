# Recréation du script après le reset de l'environnement

script = """
import subprocess
import json

# Configuration
ORG_URL = "https://dev.azure.com/<ton-organisation>"
OUTPUT_FILE = "matching_projects.txt"

def run_az(command):
    result = subprocess.run(["az"] + command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise Exception(f"Erreur: {result.stderr}")
    return result.stdout.strip()

def get_all_projects():
    output = run_az(["devops", "project", "list", "--org", ORG_URL, "--query", "value[].name", "-o", "tsv"])
    return output.splitlines()

def get_repos(project):
    output = run_az(["repos", "list", "--project", project, "--org", ORG_URL, "--query", "[].name", "-o", "tsv"])
    return output.splitlines()

def get_yaml_files(project, repo):
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

def search_pipeline_task(project, repo, file_path, keyword):
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

    with open(OUTPUT_FILE, "w") as f:
        for proj in sorted(matching_projects):
            f.write(f"{proj}\\n")

    print(f"\\n📄 Projets sauvegardés dans {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
"""

script_path = "/mnt/data/check_iaaspipeline_usage_to_file.py"
with open(script_path, "w") as f:
    f.write(script)

script_path
