# 📖 Documentation Technique – Tâche Azure DevOps – SnapLogic Graduation

---

## 1. Introduction & Vue d’ensemble

Cette tâche personnalisée Azure DevOps a été développée exclusivement pour automatiser le déclenchement de déploiements sur la plateforme SnapLogic, via son API REST sécurisée.

**Tout le design du projet (client TypeScript généré à partir du contrat OpenAPI, gestion du token OIDC, logique des inputs, etc.) est entièrement orienté SnapLogic.**

La tâche gère :
- L’authentification OIDC et l’appel sécurisé de l’API SnapLogic
- Le polling du statut de déploiement jusqu’à complétion
- La cohérence stricte des environnements (DEV, QA, PROD)
- La robustesse et la traçabilité des actions dans le pipeline

**Technologies principales :**
- TypeScript, Node.js, Azure DevOps, OpenAPI, Service Connection OIDC/custom

---

## ⚠️ Migration et remplacement d’une tâche existante SnapLogic

> **Contexte :**
> Cette version remplace une tâche SnapLogic déjà déployée dans l’organisation. Le fichier `task.json` conserve **l’identifiant (`id`) de la tâche existante** afin d’assurer une migration transparente pour tous les pipelines qui l’utilisent.
>
> **Pourquoi ce choix ?**
> - Les pipelines Azure DevOps référencent la tâche par son `id` : aucune modification côté utilisateurs finaux.
> - L’historique, les permissions et les configurations existantes sont conservés.
> - Seule la logique, la sécurité et l’intégration sont modernisées.
>
> **Bonnes pratiques pour les développeurs :**
> - Ne jamais changer l’`id` dans `task.json`.
> - Mettre à jour la version (`version.Major.Minor.Patch`) à chaque évolution significative.
> - Documenter les changements dans le changelog ou la documentation technique.

---

## 2. Architecture & Flux global

```
[Pipeline Azure DevOps]
      |
      v
[Tâche custom TypeScript]
      |
      v
[Client généré OpenAPI]
      |
      v
[API REST SnapLogic]
```

---

## 3. Génération et gestion du client OpenAPI

- Le contrat OpenAPI fourni par SnapLogic est la seule source de vérité pour l’interface technique.
- À chaque build, le client TypeScript est régénéré automatiquement (voir section build).
- Aucune modification manuelle du code généré n’est autorisée.

---

## 4. Architecture du Projet

```
custom-task/
├── devops/                         # Pipelines CI/CD (NexusV2)
│   ├── custom-task-ci.yml              # Pipeline CI : build, lint, tests, package
│   ├── custom-task-cd-stages.yaml      # Stages et jobs de déploiement
│   └── custom-task-cd.yaml             # Pipeline CD : inclut les templates de sécurité/réglementation + appel du template local
├── src/                            # Code source TypeScript de la tâche
│   ├── client/                         # Client OpenAPI généré automatiquement
│   │   ├── api/                          # Fichiers d'API générés (GraduationApi, Status, etc.)
│   │   └── model/                        # Modèles de données générés
│   ├── test/                           # Tests unitaires et mocks
│   │   └── task.test.ts                   # Cas de test principaux
│   ├── GraduationTask.ts               # Logique principale de la tâche personnalisée
│   ├── index.ts                        # Point d'entrée de la tâche (run)
│   ├── package.json                    # Scripts (build, lint, test) utilisés en CI, dépendances, config tests unitaires
│   ├── task.json                       # Déclaration de la tâche Azure DevOps
│   └── tsconfig.json                   # Configuration TypeScript
├── openapi.yaml                      # Contrat OpenAPI SnapLogic (source de génération du client)
├── README.md                         # Documentation utilisateur et technique
└── 
```

---

## 3. Fonctionnement de la Tâche

### Entrées principales (`task.json`)

- `source` : nom du projet source à déployer (ex : `ipaas`)
- `destination` : environnement cible (ex : `ipaas.dev1`, `ipaas.cr1`, `ipaas.pr1`)
- `entityEndpoint` : nom de la Service Connection Azure DevOps à utiliser. Ce paramètre est central : la tâche l’utilise pour :
    - Générer dynamiquement le token OIDC nécessaire à l’authentification SnapLogic
    - Récupérer dynamiquement l’URL cible de l’API SnapLogic (l’URL est stockée dans la Service Connection)
    - **Note :** Pour QA et PP, la même URL de graduation SnapLogic est utilisée (mais chaque env a sa propre SC). PR utilise une URL différente et sa propre SC.

> **Remarque :** Les Service Connections utilisées doivent être de **type custom** (Azure DevOps). Pour la procédure de création/configuration, voir la page interne « url ».

**Variables pipeline utilisées** :
- `SYSTEM_TEAMPROJECT`, `SYSTEM_TEAMFOUNDATIONCOLLECTIONURI`, `BUILD_BUILDID`, `BUILD_REQUESTEDFOREMAIL` (pour le contexte release)

### Étapes principales

1. **Récupération des inputs et variables**
2. **Vérification de la cohérence environnementale**  
   (destination, URL et Service Connection doivent cibler le même env)
3. **Initialisation du client SnapLogic (OpenAPI)**
4. **Injection du token OIDC dans le client**
5. **Appel de l’API SnapLogic pour déclencher le déploiement**
6. **Polling du statut du déploiement (toutes les 3s)**
7. **Logging du statut à chaque itération (mode debug recommandé)**
8. **Gestion des statuts de retour (success, failed, running)**
9. **Gestion des erreurs et logs détaillés**

---

## 4. Sécurité

- **Authentification** :  
  Utilisation d’un token OIDC fourni par une Service Connection Azure DevOps de type “Generic” ou “OIDC”.
- **Séparation stricte des environnements** :  
  La tâche vérifie que la SC, l’URL et le paramètre `destination` correspondent au même environnement (dev, cr, prd).
- **Gestion des secrets** :  
  Le token n’est jamais loggué en clair. Les inputs secrets sont marqués `isSecret` dans `task.json`.
- **Protection contre les erreurs de configuration** :  
  La tâche échoue explicitement si une incohérence est détectée (ex : SC prod sur env dev).

---

## 5. Développement

### Langages et outils

- TypeScript (target ES2020+)
- Node.js 16+ (exécution sur agent Ubuntu-latest)
- Client OpenAPI généré via :
  ```sh
  npx @openapitools/openapi-generator-cli generate -i openapi.yaml -g typescript-node -o src/client --additional-properties=useSingleRequestParameter=true,typescriptThreePlus=true
  ```
- Linting via ESLint (`npm run lint`)
- Tests unitaires via Mocha/Chai (`npm test`)

### Principaux fichiers

- `GraduationTask.ts` : logique de la tâche, gestion du polling, des erreurs, des statuts et de la sécurité.
- `client/api/graduationApi.ts` : client généré, méthodes `deploy`, `getStatusById`, injection du token via `accessToken`.
- `test/task.test.ts` : tests unitaires avec mocks du client généré.

### Gestion des dépendances

- Dépendances Node.js : `azure-devops-node-api`, `azure-pipelines-task-lib`, `request`, etc.
- Toutes les dépendances sont listées dans `package.json`.

---

## 6. Déploiement et Packaging

### Compilation

- Compile le code TypeScript en JavaScript avant publication :
  ```sh
  npm run build
  ```
- Le JS compilé est placé dans `dist/`.

### Packaging

- Le package de la tâche doit contenir :
  - JS compilé (`dist/`)
  - `task.json`
  - `node_modules` (ou les dépendances nécessaires)
  - Client OpenAPI généré (ne jamais éditer manuellement)
- Utilisation de `tfx` pour packager et publier la tâche sur Azure DevOps.

### Publication

- Publier la tâche sur l’organisation Azure DevOps via :
  ```sh
  tfx build tasks upload --task-path .
  ```

---


## 5. CI/CD

### 5.1. Automatisation DevSecOps (CI/CD NexusV2)

#### Contexte DevSecOps & NexusV2

Cette tâche a été conçue pour s’intégrer dans le modèle DevSecOps “NexusV2” utilisé chez le client. Le répertoire `devops/` à la racine du projet contient tout le nécessaire pour automatiser le build et le déploiement de la tâche elle-même, selon les standards de sécurité et de conformité de l’organisation.

#### Structure du répertoire `devops/`

```
devops/
├── custom-task-ci.yml            # Pipeline CI : build, lint, tests, package
├── custom-task-cd.yaml           # Pipeline CD : inclut les templates de sécurité/réglementation de l’organisation + appel du template local
├── custom-task-cd-stages.yaml    # Template local : stages et jobs de déploiement de la tâche
```

- **custom-task-ci.yml** : Compile, teste et package la tâche (lint, scan de vulnérabilités, etc.).
- **custom-task-cd.yaml** : Compose le pipeline de déploiement en important les templates de sécurité de l’organisation (autres repos) + appelle le template local.
- **custom-task-cd-stages.yaml** : Définit les stages et jobs de déploiement (publication de la tâche, gestion des artefacts, etc.).

#### Exemple d’inclusion de templates dans `custom-task-cd.yaml`

```yaml
# Exemple d’inclusion d’un template sécurité organisationnel + appel du template local
extends:
  template: path/to/org/security-template.yaml@securityRepo

stages:
  - template: custom-task-cd-stages.yaml
```

#### Points d’attention

- **Conformité NexusV2** : Les pipelines CI/CD doivent respecter les exigences de NexusV2 (scans, approbations, publication contrôlée, etc.).
- **Séparation des responsabilités** : Ton équipe est responsable du déploiement de la tâche elle-même, tandis que l’équipe SnapLogic consommera la tâche dans ses propres pipelines.
- **Variables d’environnement, secrets, permissions** : À documenter selon les besoins du pipeline et les standards du client.

### 5.2. Qualité & tests

- **Tests unitaires** :  
  Couvrent les cas de succès, d’erreur, de polling, de gestion des statuts et de cohérence des inputs.
- **Linting** :  
  ESLint avec configuration stricte pour garantir la cohérence du code.
- **Couverture** :  
  Viser >70% sur la logique métier critique.

### 5.3. Packaging & build

- Compile le code TypeScript en JavaScript avant publication :
  ```sh
  npm run build
  ```
- Le JS compilé est placé dans `dist/`.

#### Packaging

- Le package de la tâche doit contenir :
  - JS compilé (`dist/`)
  - `task.json`
  - `node_modules` (ou les dépendances nécessaires)
  - Client OpenAPI généré (ne jamais éditer manuellement)
- Utilisation de `tfx` pour packager et publier la tâche sur Azure DevOps.

#### Publication

- Publier la tâche sur l’organisation Azure DevOps via :
  ```sh
  tfx build tasks upload --task-path .
  ```

### 5.4. Déploiement de la tâche

- Description des stages et jobs de déploiement dans `custom-task-cd-stages.yaml`.
- Publication sur Azure DevOps via les pipelines NexusV2.

---

## 6. Gestion des environnements

- **Logique de graduation multi-environnements** :
  - La tâche permet d’orchestrer une chaîne de promotions : de DV (développement) vers QA, de QA vers PP, puis de PP vers PR.
  - Pour les environnements QA et PP, l’URL de graduation SnapLogic est identique (même endpoint), mais chaque environnement utilise sa propre Service Connection custom pour garantir l’isolation des accès.
  - L’environnement PR (production) dispose d’une URL de graduation distincte et d’une Service Connection dédiée.
- **Validation stricte** :
  - À chaque exécution, la tâche vérifie la cohérence entre l’URL extraite de la Service Connection, la valeur de `destination` et le nom de la Service Connection.
  - Toute incohérence (mauvaise URL, SC ou destination) entraîne un échec immédiat (“fail-fast”).

> **Remarque pour les développeurs** :
> La logique de mapping entre environnement, Service Connection et URL est centralisée dans le code. Si la matrice d’environnements évolue, il faudra adapter cette logique.

---

## 10. Logging et Debug

- Utiliser `tl.debug()` pour les logs détaillés.
- Activer le mode debug dans le pipeline pour voir les logs en temps réel :
  - Ajouter la variable pipeline : `System.Debug=true`
- Les logs de polling sont visibles à chaque itération en mode debug.

---

## 11. Maintenance et évolution

- **Pour régénérer le client OpenAPI** :  
  Voir la commande en section développement.  
  Ne jamais éditer le code généré à la main.
- **Pour ajouter un nouvel environnement** :  
  Ajouter la logique de détection dans la fonction de cohérence.
- **Pour migrer vers une nouvelle version d’API** :  
  Mettre à jour le fichier `openapi.yaml` et régénérer le client.
- **Pour ajouter des tests** :  
  Ajouter des cas dans `test/task.test.ts` en mockant le client généré.

---

## 12. Sécurité et bonnes pratiques DevOps

- **Jamais de secrets en clair dans les logs ou le code.**
- **Respect des permissions minimales** sur les Service Connections.
- **Versioning sémantique** de la tâche (`task.json`).
- **Documentation** à jour : README et documentation technique.
- **Accessibilité et robustesse** : gestion des erreurs explicites, messages clairs, respect des standards Azure DevOps.

---

## 13. Annexes

### Ressources utiles

- [Azure DevOps Custom Tasks](https://learn.microsoft.com/en-us/azure/devops/extend/develop/add-build-task)
- [OpenAPI Generator](https://openapi-generator.tech/)
- [azure-devops-node-api](https://github.com/microsoft/azure-devops-node-api)
- [azure-pipelines-task-lib](https://github.com/microsoft/azure-pipelines-task-lib)
- [ESLint](https://eslint.org/)
- [Mocha](https://mochajs.org/)
- [Chai](https://www.chaijs.com/)

---

## 14. Rappel technique SnapLogic

Tout le code, la génération du client et la gestion du token OIDC sont strictement dédiés à l’intégration avec SnapLogic : aucun usage générique n’est prévu.

---

## 15. Documentation DevOps – Déploiement de la tâche (NexusV2)

### 15.1. Contexte DevSecOps & NexusV2

Cette tâche a été conçue pour s’intégrer dans le modèle DevSecOps “NexusV2” utilisé chez le client. Le répertoire `devops/` à la racine du projet contient tout le nécessaire pour automatiser le build et le déploiement de la tâche elle-même, selon les standards de sécurité et de conformité de l’organisation.

### 15.2. Structure du répertoire `devops/`

```
devops/
├── custom-task-ci.yml            # Pipeline CI : build, lint, tests, package
├── custom-task-cd.yaml           # Pipeline CD : inclut les templates de sécurité/réglementation de l’organisation + appel du template local
├── custom-task-cd-stages.yaml    # Template local : stages et jobs de déploiement de la tâche
```

- **custom-task-ci.yml** : Compile, teste et package la tâche (lint, scan de vulnérabilités, etc.).
- **custom-task-cd.yaml** : Compose le pipeline de déploiement en important les templates de sécurité de l’organisation (autres repos) + appelle le template local.
- **custom-task-cd-stages.yaml** : Définit les stages et jobs de déploiement (publication de la tâche, gestion des artefacts, etc.).

### 15.3. Exemple d’inclusion de templates dans `custom-task-cd.yaml`

```yaml
# Exemple d’inclusion d’un template sécurité organisationnel + appel du template local
extends:
  template: path/to/org/security-template.yaml@securityRepo

stages:
  - template: custom-task-cd-stages.yaml
```

### 15.4. Points d’attention

- **Conformité NexusV2** : Les pipelines CI/CD doivent respecter les exigences de NexusV2 (scans, approbations, publication contrôlée, etc.).
- **Séparation des responsabilités** : Ton équipe est responsable du déploiement de la tâche elle-même, tandis que l’équipe SnapLogic consommera la tâche dans ses propres pipelines.
- **Variables d’environnement, secrets, permissions** : À documenter selon les besoins du pipeline et les standards du client.

---

## 16. Contact et support

Pour toute question technique, contacter :  
- **Equipe DevOps** : dev_sup_integration@zz.com

---

**Cette documentation est à intégrer dans le README du projet et à maintenir à jour à chaque évolution majeure.**
