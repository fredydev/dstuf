# 📖 Documentation Technique – Tâche Azure DevOps SnapLogic Graduation

---

## 1. Notice

> **Cette documentation s’adresse exclusivement aux développeurs et mainteneurs de la tâche. Elle ne couvre pas l’utilisation dans les pipelines utilisateurs finaux.**

---

## 2. Objectif

Déclencher et superviser des déploiements SnapLogic via une API REST sécurisée, dans un contexte DevSecOps automatisé (NexusV2).

---

## 3. Contexte & historique

- Remplacement d’une tâche existante (même `id` dans `task.json` pour migration transparente).
- Modernisation complète : gestion OIDC, client généré, sécurité renforcée, gestion stricte des environnements.
- Compatible avec les pipelines existants sans modification.

> **Bonnes pratiques migration :**
> - Ne jamais changer l’`id` dans `task.json`.
> - Mettre à jour la version (`version.Major.Minor.Patch`) à chaque évolution significative.
> - Documenter les changements majeurs.

---

## 4. Architecture du projet

```
custom-task/
├── devops/
│   ├── custom-task-ci.yml              # Pipeline CI : build, lint, tests, package
│   ├── custom-task-cd-stages.yaml      # Stages et jobs de déploiement
│   └── custom-task-cd.yaml             # Pipeline CD : inclut les templates sécurité/org
├── src/
│   ├── client/                         # Client OpenAPI généré automatiquement
│   │   ├── api/                        # Fichiers d'API générés
│   │   └── model/                      # Modèles de données générés
│   ├── test/                           # Tests unitaires et mocks
│   │   └── task.test.ts                # Cas de test principaux
│   ├── GraduationTask.ts               # Logique principale
│   ├── index.ts                        # Point d'entrée (run)
│   ├── package.json                    # Scripts (build, lint, test), dépendances, config tests unitaires
│   ├── task.json                       # Déclaration de la tâche Azure DevOps
│   └── tsconfig.json                   # Configuration TypeScript
├── openapi.yaml                        # Contrat OpenAPI SnapLogic (source de génération du client)
├── README.md                           # Documentation
```

- **Contrat OpenAPI** : source de vérité, génération automatique du client TypeScript, conformité API garantie.
- **Répertoire devops/** : pipelines CI/CD, versionning, packaging, publication.

---

## 5. Entrées et sorties de la tâche

### Inputs (`task.json`)
- `source` : Projet source à déployer (ex : `ipaas`)
- `destination` : Environnement cible (`ipaas.dev1`, `ipaas.qa1`, `ipaas.pr1`)
- `entityEndpoint` : Nom de la Service Connection custom (OIDC + URL API)
  - Génération dynamique du token OIDC
  - Récupération dynamique de l’URL cible
  - Pour QA/PP, même URL mais SC distinctes ; PR a sa propre URL et SC

> **Remarque** : Les Service Connections doivent être de type custom.

### Outputs
- Statut de déploiement SnapLogic (succès/échec)
- Logs détaillés (mode debug activable)

---

## 6. Prérequis & dépendances

- **Node.js** : v16+
- **TypeScript** : target ES2020+
- **Azure DevOps agent** : Ubuntu-latest
- **Packages principaux** :
  - `azure-pipelines-task-lib`
  - `azure-devops-node-api`
  - Client OpenAPI généré via `@openapitools/openapi-generator-cli`
  - `request` (pour le client généré)
- **Service Connection** : custom (OIDC/generic), URL cible configurée

---

## 7. Processus CI/CD (build, test, packaging, publication)

- Orchestration complète via pipeline CI/CD (`devops/custom-task-ci.yml`)
  - Synchronisation de version (`package.json`, `task.json`, pipeline)
  - Génération du client, compilation, lint, tests, packaging, nettoyage des dépendances, publication
  - Sécurité : secrets masqués dans les logs
  - Qualité : tous les tests, lint et build via `npm run ci:all`

---

## 8. Versionning & migration

- L’`id` de la tâche dans `task.json` reste inchangé pour migration transparente.
- Version (`major`, `minor`, `patch`) synchronisée automatiquement avec le pipeline CI/CD.
- Pipelines existants bénéficient automatiquement de la nouvelle version.
- **Bonnes pratiques** :
  - Ne jamais baisser la version
  - Documenter les changements majeurs

---

## 9. Sécurité & bonnes pratiques

- Aucun secret n’est loggué en clair
- Inputs secrets marqués `isSecret` dans `task.json`
- Vérification stricte de la cohérence SC/URL/destination
- Échec explicite en cas d’incohérence
- Respect des permissions minimales sur les Service Connections

---

## 10. Maintenance & évolution

- Regénérer le client OpenAPI à chaque changement du contrat
- Adapter la logique de mapping pour tout nouvel environnement
- Mettre à jour la documentation et le changelog à chaque évolution majeure

---

## 11. Annexes

- **Contact technique** : dev_sup_integration@zz.com
- **Changelog** : voir fichier dédié ou section en fin de doc
- **Liens utiles** :
  - [Documentation OpenAPI](https://swagger.io/specification/)
  - [Azure DevOps Custom Tasks](https://learn.microsoft.com/en-us/azure/devops/extend/develop/add-build-task)
