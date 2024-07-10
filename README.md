# Bot Martial
Le bot discord Martial est l'un des bots discord tout en un les plus sophistiqués et complets avec plus de 150 commandes. Ce bot regorge de divers fonctionnalités, tels que :
- Giveaways
- Modération
- Informations
- Antiraid
- Auto-Modération
- Musique
- Backup
- Permission
- Ticket
- Logs
- Vocaux temporaires
- Commandes personnalisées
Et bien plus encore! À vous de le découvrir 😎.

# À noter
Afin d'utiliser ce code source, vous êtes soumis à **des conditions**.
Dans toutes vos copies vous devrez citer : 
`"This software includes work by GSenkoo (github)"`

# Guide de configuration
### 1. Fichier ".env"
Créez un fichier nommé ".env" et y-ajouez y les lignes suivantes :
```
TOKEN = votre_token_ici

MYSQL_USER = votre_identifiant_mysql
MYSQL_PASSWORD = votre_mot_de_passe_mysql
MYSQL_HOST = votre_host
MYSQL_DB = le_nom_de_votre_db

DEEPL_KEY = votre_clée_deepl
GOOGLE_API_SEARCH_KEY = votre_clee_api_google
GOOGLE_API_SEARCH_CSE = votre_clee_de_recherche
```

**En Remplaçant :**
- **`votre_token_ici`** par  *[Le token de votre bot](https://youtu.be/aI4OmIbkJH8?si=RyxOBtSf6JENda9P)*
- **`votre_identifiant_mysql`** par *[Un idenfiant de compte local mysql](https://www.youtube.com/watch?v=5h5IKUjAO24)*
- **`votre_mot_de_passe_mysql`** par *[Le mot de passe du compte local mysql donnée](https://www.youtube.com/watch?v=5h5IKUjAO24)*
- **`votre_clée_deepl`** par *[Une clée deepl](https://www.deepl.com/fr/pro#developer)*
- **`votre_host`** par votre host mysql (ex: localhost)
- **`le_nom_de_votre_db`** par le nom de votre base de donnée
- **`votre_clee_api_google`** par *[Une clée api google](https://developers.google.com/custom-search/v1/overview?hl=fr)*
- **`votre_clee_de_recherche`** par *[Une clée de recherche google](https://programmablesearchengine.google.com/)*

### 2. Fichier "config.json"
Tout en haut du fichier "config.json", vous pouvez voir une clée "developers" accompagnée en valeurs, d'une liste.
Normalement. Si vous avez une bonne vue, vous voyez ça tout en haut :
```json
{
    "developers": [1213951846234726441],
    ...
}
```
Dans cette liste, vous pouvez votre ID discord et/ou celui d'autres personnes. Les utilateurs dont leurs noms sont dans cette liste ont toutes les permissions sur le bot. *N'Envisagez pas de mettre trop de personne dans la liste, ça risque de causer des problèmes*.

### 3. Installations
Pour utiliser ce bot, vous aurez biensûr besoin de [Python 3.11](https://www.python.org/downloads/release/python-3119/) (Exactement cette version). Dans votre console (Windows), exécutez cette commande pour directement installer tous les packages nécessaires :
```
pip install -r requirements.txt
```
Ou alors, regardez les requirements ci-dessous et installez les manuellements.

# Requirements (avec Python et Mysql)
 - py-cord (version suppérieur ou égal à `2.5.0`)
 - aiomysql (version suppérieur ou égal à `0.2.0`)
 - python-dotenv (version suppérieur ou égal à `1.0.1`)
 - cryptography (version suppérieur ou égal à `42.0.8`)
 - PyMySQL (version suppérieur ou égal à `1.1.1`)
 - typing_extensions (version suppérieur ou égal à `4.11.0`)
 - sympy (version suppérieur ou égal à `1.12`)
 - psutil (version suppérieur ou égal à `6.0.0`)
 - wikipedia (version suppérieur ou égal à `1.4.0`)
 - deepl (version suppérieur ou égal à `1.18.0`)

# Lancer votre bot (Visual Studio Code)
Vous devez vous rendre dans le fichier `main.py`, ensuite, dans le menu tout en haut, utilisez `Run > Start Debugging`