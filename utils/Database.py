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

import threading
import time
import aiomysql
import os
import dotenv
import json
import warnings

dotenv.load_dotenv()

class Database:
    """
    Skibidi Bob
    --------------------------------------------
    """
    def __init__(self):
        self.pool = None

    async def create_pool(self):
        """
        Créer un pool
        """
        assert not self.pool

        pool = await aiomysql.create_pool(
            host = os.getenv("MYSQL_HOST"),
            user = os.getenv("MYSQL_USER"),
            password = os.getenv("MYSQL_PASSWORD"),
            db = os.getenv("MYSQL_DB"),
            minsize = 1,
            maxsize = 10
        )
    
        self.pool = pool


    async def close_pool(self):
        """
        Supprimer la connection actuelle.
        --------------------------------------------
        """
        assert self.pool

        self.pool.close()
        await self.pool.wait_closed()
        
        self.pool = None


    async def intialize(self, intialize_tables : list = []) -> None:
        """
        Intialiser la base de donner.

        Arguments
        --------------------------------------------
        intialize_tables `list`, default `[]` :
            Des noms de tables qui seront réinitialisées

        Return
        --------------------------------------------
        `None`
        """
        assert os.path.exists("config.json")
        assert os.path.isfile("config.json")

        warnings.simplefilter("ignore")

        async with self.pool.acquire() as connection:
            async with connection.cursor() as cursor:
                with open("config.json", encoding = "utf-8") as file:
                    config_data = json.load(file)
                    tables_data = config_data["tables"]


                for table_name, table_data in tables_data.items():
                    assert table_data
                    assert table_data.get("primary_keys", None)
                    assert table_data.get("keys", None)

                    if table_name in intialize_tables:
                        await cursor.execute(f"DROP TABLE IF EXISTS {table_name}")

        # --------------------- Ajouter les tables concernés si elles ne sont pas présentes --------------------- #
                    keys_values = ",\n".join([
                        f"{keys} {info}" for keys, info in {**table_data["primary_keys"], **table_data["keys"]}.items()
                    ])
                    keys_values += f",\nPRIMARY KEY ({', '.join(table_data['primary_keys'].keys())})"
                    await cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (\n{keys_values}\n)")

        # --------------------- Créer/Supprimer une colonne si nécessaire --------------------- #
                    await cursor.execute(f"SHOW COLUMNS FROM {table_name}")
                    columns_data = await cursor.fetchall()
                    columns_in_table = []
                    table_official_columns = list(table_data["primary_keys"].keys()) + list(table_data["keys"].keys())
                    
                    for column_data in columns_data:
                        column_name = column_data[0]
                        columns_in_table.append(column_name)
                        if column_name not in table_official_columns:
                            await cursor.execute(f"ALTER TABLE {table_name} DROP COLUMN {column_name}")
                    
                    for column_name in table_official_columns:
                        if column_name not in columns_in_table:
                            if column_name in table_data["primary_keys"].keys():
                                await cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {table_data['primary_keys'][column_name]}")
                            else:
                                await cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {table_data['keys'][column_name]}")

        # --------------------- Supprimmer les tables inutiles --------------------- #
                await cursor.execute("SHOW TABLES")
                result = await cursor.fetchall()
                result = [x[0] for x in result]
                for table_name_into in result:
                    if table_name_into not in tables_data.keys():
                        await cursor.execute(f"DROP TABLE {table_name_into}")

            await connection.commit()

    
    async def execute(self, code : str, data : tuple = None, fetch : bool = False, commit : bool = True):
        async with self.pool.acquire() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(code, data)
                if fetch:
                    result = await cursor.fetchall()
                    return result


    async def set_data(self, table : str, column : str, new_value, commit : bool = True, **keys_indicator) -> None:
        """
        Possibilitée 1 : Insérer une donnée
        Possibilitée 2 : Mettre à jour une donnée

        Arguments
        --------------------------------------------
        table `str` :
            Le nom de la table
        column `str` : 
            Le nom de la colonne
        new_value :
            La nouvelle valeur que vous souhaitez donner au row
        keys_indicator `key word arguments` :
            Les clées primaires
        
        Return
        --------------------------------------------
        `None`

        Exemple d'utilisation
        --------------------------------------------
        ```
        await set_data("guild", "theme", 0xFFFFFF, guild_id = 123)
        ```
        """
        async with self.pool.acquire() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(
                    f"INSERT INTO {table}({', '.join(keys_indicator.keys())}, {column}) VALUES ({'%s, ' * len(keys_indicator.keys())}%s)"
                    + f"ON DUPLICATE KEY UPDATE {column} = %s",
                    tuple([value for value in keys_indicator.values()] + [new_value, new_value])
                )
            if commit:
                await connection.commit()


    async def get_data(self, table : str, column : str, list_value : bool = False, dict_value : bool = False, **keys_indication):
        """
        Obtenir une donnée. Si la donnée n'éxiste pas, alors la valeur par défaut de la colonne sera renvoyée.

        Arguments
        --------------------------------------------
        table `str` :
            Le nom de votre table
        column `str` :
            Le colonne de la valeur que vous souhaitez obtenir dans la table
        keys_indicator `key word arguments` :
            Les clées primaires

        Return
        --------------------------------------------
        `Your data value` (ou alors, la valeur par défaut)

        Exemple d'utilisation
        --------------------------------------------
        ```  
        await get_data("guild", "theme", guild_id = 123)
        ```
        """
        assert not (list_value and dict_value)

        async with self.pool.acquire() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(
                    f"SELECT {column} FROM {table} WHERE {' AND '.join([f'{key} = %s' for key in keys_indication.keys()])}", 
                    tuple([value for value in keys_indication.values()])
                )
                result = await cursor.fetchone()
                if result:
                    await cursor.close()
                    response = result[0]
                else:
                    await cursor.execute(f"SHOW COLUMNS FROM {table}")
                    columns_data = await cursor.fetchall()
                    await cursor.close()
                    for column_data in columns_data:
                        if column_data[0] == column:
                            response = column_data[4]
                
                if list_value:
                    if not response: response = "[]"
                    return json.loads(response)
                if dict_value:
                    if not response: response = "{}"
                    return json.loads(response)
                return response


    async def get_table_columns(self, table : str) -> list:
        async with self.pool.acquire() as connection:
            async with connection.cursor() as cursor:  
                await cursor.execute(f"SHOW COLUMNS FROM {table}")
                columns = [column_data[0] for column_data in await cursor.fetchall()]
                await cursor.close()
                
                return columns