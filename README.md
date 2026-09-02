# Verificator

Plateforme Flask locale permettant de déposer un fichier Python et d'exécuter les tests préparés par l'enseignant.

## Lancement local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:FLASK_APP = "verificator:create_app"
flask run --debug
```

Ouvrir http://127.0.0.1:5000. Un exemple est disponible pour la séance 2, exercice `moyenne`.

## Vérifications proposées

Les tests unitaires peuvent être lancés avec `python -m pytest`. Aucun test ni build n'est lancé automatiquement par le projet.

## Déploiement Render / Docker

Le prototype peut être déployé avec le `Dockerfile` fourni. En production publique, l'exécution étudiante doit être renforcée : image Docker sans réseau, utilisateur non privilégié, limites CPU/mémoire/PIDs, filesystem en lecture seule et timeout côté orchestrateur. Le processus séparé actuel est une barrière de prototype, pas une sandbox suffisante à lui seul.

## Ajouter un exercice

Créer un module dans `verificator/exercises/`, y déclarer un objet `Exercise` avec `test_file(path)`, puis l'ajouter à `EXERCISES` dans `verificator/exercises/__init__.py`. Les tests doivent retourner une liste de dictionnaires `{name, passed, message}`.

## Limites et prochaines étapes

Le prototype n'utilise ni compte ni base de données. Les fichiers sont temporaires et supprimés après traitement. Avant une mise en ligne publique, utiliser une sandbox Docker dédiée ou un service d'exécution isolé, appliquer des quotas et journaliser les exécutions sans conserver le code étudiant.

### Protection par mot de passe

Dans Render, définir `VERIFICATOR_PASSWORD` et `VERIFICATOR_SECRET_KEY`. Le mot de passe ne doit jamais être écrit dans le dépôt. Utiliser HTTPS ainsi qu'un mot de passe long et unique. Si le mot de passe est absent, l'application refuse l'accès avec une erreur 503.
