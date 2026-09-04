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

## QCM de début de séance

La page `/qcm`, accessible depuis la navigation, permet aux étudiants de saisir leur nom et prénom et de répondre à 15 questions, avec un choix obligatoire parmi A, B, C et D pour chaque question. Les énoncés et les propositions sont présentés par l'enseignant en cours ; la page sert de feuille de réponses, sans notation automatique. Elle utilise la même protection par mot de passe que le correcteur Python.

Après validation côté serveur, chaque envoi est enregistré dans `instance/qcm.sqlite3`, dans la table `qcm_submissions` : identifiant, nom, réponses au format JSON (numéros de questions associés aux lettres) et date UTC. Un message confirme l'enregistrement ; actualiser la page de confirmation ne renvoie pas les réponses. Plusieurs envois du même nom restent possibles et sont conservés séparément.

La base est créée au premier envoi et exclue du dépôt Git. Pour consulter les réponses, ouvrir la base avec un lecteur SQLite. Sur Render ou Docker, configurer `VERIFICATOR_QCM_DATABASE` vers un fichier sur un disque ou volume persistant pour conserver les réponses après un redéploiement.

Les tests de cette page sont dans `tests/test_qcm.py` et peuvent être lancés avec `python -m pytest tests/test_qcm.py`, après accord explicite.

## Déploiement Render / Docker

Le prototype peut être déployé avec le `Dockerfile` fourni. En production publique, l'exécution étudiante doit être renforcée : image Docker sans réseau, utilisateur non privilégié, limites CPU/mémoire/PIDs, filesystem en lecture seule et timeout côté orchestrateur. Le processus séparé actuel est une barrière de prototype, pas une sandbox suffisante à lui seul.

## Ajouter un exercice

Créer un module dans `verificator/exercises/`, y déclarer un objet `Exercise` avec `test_file(path)`, puis l'ajouter à `EXERCISES` dans `verificator/exercises/__init__.py`. Les tests doivent retourner une liste de dictionnaires `{name, passed, message}`.

## Limites et prochaines étapes

Le prototype n'utilise pas de comptes individuels. Seules les réponses au QCM sont conservées dans une base SQLite. Les fichiers Python sont temporaires et supprimés après traitement. Avant une mise en ligne publique, utiliser une sandbox Docker dédiée ou un service d'exécution isolé, appliquer des quotas et journaliser les exécutions sans conserver le code étudiant.

### Protection par mot de passe

Dans Render, définir `VERIFICATOR_PASSWORD` et `VERIFICATOR_SECRET_KEY`. Le mot de passe ne doit jamais être écrit dans le dépôt. Utiliser HTTPS ainsi qu'un mot de passe long et unique. Si le mot de passe est absent, l'application refuse l'accès avec une erreur 503.
