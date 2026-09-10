# Verificator

Plateforme Flask locale permettant de déposer un fichier Python et d'exécuter les tests préparés par l'enseignant.

Chaque vérification Python exige le nom et prénom de l'étudiant. Avant d'afficher la correction, l'application enregistre dans `instance/qcm.sqlite3` le nom, l'adresse IP de la requête, l'exercice choisi, le contenu du programme, sa réussite ou son échec et la date UTC. Si l'enregistrement échoue, le résultat n'est pas affiché afin que l'historique enseignant reste complet.

## Lancement local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:FLASK_APP = "verificator:create_app"
flask run --debug
```

Ouvrir http://127.0.0.1:5000. Les exercices des séances 2 et 3 sont disponibles
dans l'ordre des TD.

## Vérifications proposées

Les tests unitaires peuvent être lancés avec `python -m pytest`. Aucun test ni build n'est lancé automatiquement par le projet.

## QCM de début de séance

La page `/qcm`, accessible depuis la navigation, permet aux étudiants de saisir leur nom et prénom et de répondre à 15 questions, avec un choix obligatoire parmi A, B, C et D pour chaque question. Les énoncés et les propositions sont présentés par l'enseignant en cours ; la page sert de feuille de réponses, avec notation dans l'espace enseignant selon le questionnaire et la version A/B choisis. Elle utilise la même protection par mot de passe que le correcteur Python.

Après validation côté serveur, chaque envoi est enregistré dans `instance/qcm.sqlite3`, dans la table `qcm_submissions` : identifiant, nom, réponses au format JSON (numéros de questions associés aux lettres) et date UTC. Un message confirme l'enregistrement ; actualiser la page de confirmation ne renvoie pas les réponses. Plusieurs envois du même nom restent possibles et sont conservés séparément.

La base est créée au premier envoi et exclue du dépôt Git. Pour consulter les réponses, utiliser l'espace enseignant décrit ci-dessous. Sur Render ou Docker, configurer `VERIFICATOR_QCM_DATABASE` vers un fichier sur un disque ou volume persistant pour conserver les réponses après un redéploiement. La page enseignant et l'export CSV ne rendent pas ce stockage persistant : exporter les réponses avant tout redéploiement si aucun volume persistant n'est configuré.

Les tests de cette page sont dans `tests/test_qcm.py` et peuvent être lancés avec `python -m pytest tests/test_qcm.py`, après accord explicite.

### Consulter et exporter les réponses

Définir `VERIFICATOR_TEACHER_PASSWORD` dans les variables d'environnement (Render : service Verificator, **Environment**). Choisir un mot de passe privé, différent de `VERIFICATOR_PASSWORD`, et conserver une valeur privée aléatoire pour `VERIFICATOR_SECRET_KEY`. Aucun mot de passe ne doit être ajouté au dépôt. L'espace enseignant refuse l'accès si son mot de passe est absent ou identique au mot de passe étudiant, ou si la clé de session conserve sa valeur par défaut.

Depuis la correction Python ou `/qcm`, cliquer sur **Espace enseignant**. La connexion enseignant est indépendante de la connexion étudiant. `/enseignant/verifications` présente les vérifications Python du plus récent au plus ancien avec le nom, le résultat global en vert ou rouge, l'IP, la date, l'exercice et le programme. Les anciens envois enregistrés avant l'ajout du résultat sont indiqués comme non disponibles. `/enseignant/qcm` présente les réponses au QCM. Le bouton **Actualiser** recharge les données et **Déconnexion enseignant** ferme cet accès sans déconnecter une éventuelle session étudiant.

Le bouton **Exporter en CSV** télécharge toutes les réponses via `/enseignant/qcm/export.csv`, soumis à la même authentification. Le CSV utilise le séparateur point-virgule et l'encodage UTF-8 avec BOM pour faciliter son ouverture dans un tableur. Les noms pouvant être interprétés comme des formules sont préfixés par une apostrophe uniquement dans l'export. Les pages enseignant et les exports ne doivent pas être mis en cache par le navigateur.

Les tests de consultation, d'authentification et d'export sont dans `tests/test_teacher.py` : `python -m pytest tests/test_qcm.py tests/test_teacher.py`.

## Déploiement Render / Docker

Le `Dockerfile` lance Gunicorn avec un worker et quatre threads. Cette limite permet d'absorber plusieurs dépôts simultanés sans lancer trop de programmes étudiants sur une petite instance Render. Gunicorn accorde 30 secondes à une requête HTTP ; chaque programme étudiant dispose par défaut de 10 secondes afin de mieux supporter les ralentissements lorsque plusieurs corrections sont lancées simultanément. Ce délai peut être ajusté avec la variable d'environnement `VERIFICATOR_EXECUTION_TIMEOUT`.

En production publique, l'exécution étudiante doit être renforcée : image Docker sans réseau, utilisateur non privilégié, limites CPU/mémoire/PIDs, filesystem en lecture seule et timeout côté orchestrateur. Le processus séparé actuel est une barrière de prototype, pas une sandbox suffisante à lui seul.

## Ajouter un exercice

Créer un module dans `verificator/exercises/`, y déclarer un objet `Exercise` avec une fonction `test_module(module)`, puis l'ajouter à `EXERCISES` dans `verificator/exercises/__init__.py`. Les tests doivent retourner une liste de dictionnaires `{name, passed, message}`.

Les exercices de la séance 3 couvrent les modules, les fichiers texte et CSV,
puis les tableaux NumPy. Le correcteur crée lui-même les fichiers temporaires
nécessaires : les étudiants déposent uniquement leur fichier `s3_exN.py`.

## Limites et prochaines étapes

Le prototype n'utilise pas de comptes individuels. Les réponses au QCM et les vérifications Python sont conservées dans une base SQLite. Les fichiers Python temporaires sont supprimés après traitement, mais leur contenu reste dans l'historique enseignant. Cette conservation du nom, de l'IP et du code doit être annoncée aux étudiants et encadrée par une durée de conservation adaptée. Avant une mise en ligne publique, utiliser une sandbox Docker dédiée ou un service d'exécution isolé et appliquer des quotas.

### Protection par mot de passe

Dans Render, définir `VERIFICATOR_PASSWORD` et `VERIFICATOR_SECRET_KEY`. Le mot de passe ne doit jamais être écrit dans le dépôt. Utiliser HTTPS ainsi qu'un mot de passe long et unique. Si le mot de passe est absent, l'application refuse l'accès avec une erreur 503.

## QCM en versions A / B

Le cours projette A à gauche et B à droite. Chaque étudiant choisit explicitement
le questionnaire et sa version avant de répondre. L'espace enseignant et son
export CSV présentent le questionnaire, la version et le score ; les questions
de positionnement ne comptent pas. Les anciens envois restent sans note.

Les grilles privées `verificator/qcm_keys.json` sont exportées depuis
`data/qcm_versions.json` dans cours_python_iut, avec `export_qcm_versions.py`.
Déployer les deux dépôts ensemble après une modification des versions projetées.
Les réponses sont conservées dans leur ordre de présentation et les scores sont
enregistrés lors de l'envoi, pour ne pas changer rétroactivement avec une grille.
