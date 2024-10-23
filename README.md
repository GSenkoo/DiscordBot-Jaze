# [Archived Project] Jaze Bot
The Jaze Discord bot is a Discord bot 🤯. This bot is packed with various features, such as:
- Advanced permission system
- Comprehensive and well-organized moderation
- Suggestion system
- Welcome/farewell system
- Role menu
- Captcha
- Giveaways
- Information
- Games
And much more! It's up to you to discover it 😎.

# Setup Guide
P.S.: Since this project is abandoned for some personal reasons 😮‍💨, i did not take the time to translate it, so the source code and the bot are entirely in **French**.
### 1. ".env" File
Create a file named ".env" and add the following lines:
```
TOKEN = your_token_here

MYSQL_USER = your_mysql_username
MYSQL_PASSWORD = your_mysql_password
MYSQL_HOST = your_host
MYSQL_DB = the_name_of_your_db

DEEPL_KEY = your_deepl_key
GOOGLE_API_SEARCH_KEY = your_google_api_key
GOOGLE_API_SEARCH_CSE = your_search_key
BLAGUE_API_KEY = your_joke_api_key
```

**Replace:**
- **`your_token_here`** with *[Your bot token](https://youtu.be/aI4OmIbkJH8?si=RyxOBtSf6JENda9P)*
- **`your_mysql_username`** with *[A local MySQL account identifier](https://www.youtube.com/watch?v=5h5IKUjAO24)*
- **`your_mysql_password`** with *[The local MySQL account password given](https://www.youtube.com/watch?v=5h5IKUjAO24)*
- **`your_deepl_key`** with *[A DeepL key](https://www.deepl.com/fr/pro#developer)*
- **`your_host`** with your MySQL host (e.g., localhost)
- **`the_name_of_your_db`** with the name of your database
- **`your_google_api_key`** with *[A Google API key](https://developers.google.com/custom-search/v1/overview?hl=fr)*
- **`your_search_key`** with *[A Google search key](https://programmablesearchengine.google.com/)*
- **`your_joke_api_key`** with *[A joke API key](https://www.blagues-api.fr/)*

### 2. "config.json" File
At the top of the "config.json" file, you can see a key "developers" accompanied by a list of values.
Normally, if you have good vision, you will see this at the top:
```
{
    "developers": [1213951846234726441],
    ...
}
```
In this list, you can add your Discord ID and/or those of others. Users whose names are in this list have all permissions on the bot. *Do not consider adding too many people to the list, as it may cause problems*.

### 3. Installations
To use this bot, you will of course need [Python 3.11](https://www.python.org/downloads/release/python-3119/) (exactly this version). In your console (Windows), run this command to install all the necessary packages directly: 
```
pip install -r requirements.txt
```

Alternatively, check the requirements below and install them one by one.

# Requirements (with Python and MySQL)
 - py-cord (version greater than or equal to `2.5.0`)
 - aiomysql (version greater than or equal to `0.2.0`)
 - python-dotenv (version greater than or equal to `1.0.1`)
 - cryptography (version greater than or equal to `42.0.8`)
 - PyMySQL (version greater than or equal to `1.1.1`)
 - typing_extensions (version greater than or equal to `4.11.0`)
 - sympy (version greater than or equal to `1.12`)
 - psutil (version greater than or equal to `6.0.0`)
 - wikipedia (version greater than or equal to `1.4.0`)
 - deepl (version greater than or equal to `1.18.0`)
 - blagues-api (version greater than or equal to `1.0.3`)
 - emoji (version greater than or equal to `2.12.1`)

# Run Your Bot (Visual Studio Code)
You need to go to the `main.py` file, then in the top menu, use `Run > Start Debugging`

# ⚠️ Turning Off the Bot
To properly turn off the bot and close the connection with the database, use the command `+stop`.
