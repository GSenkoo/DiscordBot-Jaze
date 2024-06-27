"""
MIT License with Attribution Clause

Copyright (c) 2024 GSenkoo

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

**Attribution:**
All copies, modifications, or substantial portions of the Software must include
the original author attribution as follows:
"This software includes work by GSenkoo (github)".

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


import discord
import os
from typing import Tuple
from datetime import datetime
from discord.ext import commands

def manage_files(
    bot: commands.Bot,
    action: str,
    command_folder: str = "gestion",
    ignored_files_names : list= []
) -> Tuple[int, int, float]:
    """
    Paramètre
    --------------------------------------------
    bot `discord.ext.commands.Bot` :
        L'instance du bot
    action `str` :
        L'action que vous souhaitez accomplir ("load" pour charger les cogs, "unload" pour les décharger)
    command_folder `str`, default `"gestion"` : 
        Le dossier dans lequel est situé vos fichiers (valeur par défaut : "gestion")
    ignored_files_names `list`, default `[]` :
        Fichiers qui seront ignorés lors du chargement/déchargement des cogs (default [])

    Returns
    --------------------------------------------
    `Tuple[int, int, float]`
        successfull_file_count (integer) : Le nombre de fichier qui ont étés chargés/déchargés
        total_file_count (integer) : Le nombre total de fichier (même ceux ignorés et ceux qui ont générés des erreurs)
        function_duration (float) : La durée d'exécution de la fonction (en secondes)

    Exemples d'utilisation
    --------------------------------------------
    ```
    # Charger les fichiers
    manage_file(my_bot_instance, "load", "my_folder_is_here")

    # Déharger les fichiers et obtenir les données de l'exécution
    sucessfull_file_count, total_file_count, function_duration = manage_file(my_bot_instance, "unload", "my_folder_is_in_this_dict")
    ```
    """
    assert action in ["load", "unload"] 
    assert os.path.exists(command_folder)

    successfull_files_count = 0
    total_files_count = 0
    previous_time = datetime.now().timestamp()

    for root, directory, files in os.walk(command_folder):
        for file in files:
            if not (file.endswith(".py")) and (file not in ignored_files_names and file.removesuffix(".py") not in ignored_files_names):
                continue

            total_files_count += 1
            
            if action == "load":
                try:
                    bot.load_extension(os.path.join(root, file[:-3]).replace(os.sep, "."))
                    successfull_files_count += 1
                    print(f"[CogLoader] File loaded: '{os.path.join(root, file[:-3])}'")
                except Exception as exception: print(f"[CogLoader] Failed to load '{os.path.join(root, file[:-3])}'\n   Error : {exception}")
            else:
                try:
                    bot.unload_extension(os.path.join(root, file[:-3]).replace(os.sep, "."))
                    successfull_files_count += 1
                    print(f"[CogLoader] File unloaded: '{os.path.join(root, file[:-3])}'")
                except Exception as exception: print(f"[CogLoader] Failed to unload '{os.path.join(root, file[:-3])}'\n    Error : {exception}")
    
    new_time = datetime.now().timestamp()
    function_duration = new_time - previous_time
    
    return successfull_files_count, total_files_count, function_duration