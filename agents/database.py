# Developed by Anthony Castillo (ComradeWolf) for Peter Mann (Pedguin)
# Last Update: 04/05/2026 (DD/MM/YYYY)

import os
from pathlib import Path
import sqlite3
import json
class Agent_Database():
    def __init__(self):
        self.__database_path = "./data"
        self.__database_name = "player_data.db"
        # self.__table_names = ['players', 'coords', 'nutrition', 'traits', 'player_traits', 'player_info', 'player_deaths', 'perks']
        self.__ready = False
        self.check_for_databases()
        # self.setup_databases()
    # end __init__
    
    def connect_to_player_data(self) -> sqlite3.Connection:
        return sqlite3.connect(os.path.join(self.__database_path, self.__database_name))
    # end connect_to_player_data

    def connect_to_world_states(self) -> sqlite3.Connection:
        return sqlite3.connect(os.path.join(self.__database_path, "world_state.db"))
    # end connect_to_world_states

    def check_for_databases(self) -> None:
        if not Path(self.__database_path).is_dir(): # Create local player data directory if it doesn't exist
            Path(self.__database_path).mkdir()
        self.setup_basic_tables()
    # end check_for_databases

    def setup_basic_tables(self) -> None:
        connection = self.connect_to_player_data()
        res = connection.cursor().execute("SELECT name FROM sqlite_master")
        tables = []
        notNone = True
        while notNone:
            temp = res.fetchone()
            if temp != None:
                tables.append(temp[0])
            else:
                notNone = False
        cursor = connection.cursor()
        if "players" not in tables:
            cursor.execute('''
CREATE TABLE IF NOT EXISTS players (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username VARCHAR NOT NULL,
                            created REAL,
                            last_updated REAL
                            )
            ''')
        if "coords" not in tables:
            cursor.execute('''
CREATE TABLE IF NOT EXISTS coords (
                            player_id INTEGER PRIMARY KEY,
                            x REAL,
                            y REAL,
                            z REAL,
                            FOREIGN KEY (player_id) REFERENCES players(id)
                            )
            ''')
        if "nutrition" not in tables:
            cursor.execute('''
CREATE TABLE IF NOT EXISTS nutrition (
                           player_id INTEGER PRIMARY KEY,
                           weight INTEGER,
                           calories REAL,
                           carbohydrates REAL,
                           "proteins" REAL,
                           lipids REAL,
                           FOREIGN KEY (player_id) REFERENCES players(id)
                           )
            ''')
        if "traits" not in tables:
            cursor.execute('''
CREATE TABLE IF NOT EXISTS traits (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            trait VARCHAR NOT NULL
                            )
            ''')
        if "player_traits" not in tables:
            cursor.execute('''
CREATE TABLE IF NOT EXISTS player_traits (
                            player_id INTEGER,
                            trait_id INTEGER,
                            FOREIGN KEY (player_id) REFERENCES players(id),
                            FOREIGN KEY (trait_id) REFERENCES traits(id),
                            PRIMARY KEY (player_id, trait_id)
                            )
            ''')
        if "player_info" not in tables:
            cursor.execute('''
CREATE TABLE IF NOT EXISTS player_data (
                           player_id INTEGER PRIMARY KEY,
                           steam_id REAL,
                           server_user_id INTEGER,
                           username VARCHAR,
                           ping INTEGER,
                           display_name VARCHAR,
                           character_name VARCHAR,
                           access_level VARCHAR,
                           role VARCHAR,
                           faction VARCHAR,
                           is_alive INTEGER,
                           profession VARCHAR,
                           time_survived_float REAL,
                           time_survived_string VARCHAR,
                           zombie_kills INTEGER,
                           survivor_kills INTEGER,
                           FOREIGN KEY (player_id) REFERENCES players(id)
                           )
            ''')
        if "player_deaths" not in tables:
            cursor.execute('''
CREATE TABLE IF NOT EXISTS player_deaths (
                           player_id INTEGER,
                           timestamp REAL,
                           player_data BLOB,
                           FOREIGN KEY (player_id) REFERENCES players(id),
                           PRIMARY KEY (player_id, timestamp)
                           )
            ''')
        connection.commit()
        connection.close()
    # end setup_basic_tables

    def setup_player_tables(self, player_data_dictionary:dict) -> None:
        connection = self.connect_to_player_data()
        res = connection.cursor().execute("SELECt name FROM sqlite_master")
        tables = []
        notNone = True
        while notNone:
            temp = res.fetchone()
            if temp != None:
                tables.append(temp[0])
            else:
                notNone = False
        cursor = connection.cursor()
        if "perks" not in tables:
            perkList = []
            for perk in player_data_dictionary['perks']:
                perkList.append(f'"{perk}" IINTEGER')
            cursor.execute(f'''
CREATE TABLE IF NOT EXISTS perks (
                            player_id INTEGER PRIMARY KEY,
                            {', '.join(perkList)},
                            FOREIGN KEY (player_id) REFERENCES players(id)
                            )
            ''')
        self.__ready = True
        connection.commit()
        connection.close()
    # end setup_player_tables

    def update_player(self, player_data_dictionary:dict) -> list: # Update the player data for a given player_id
        changes = []
        connection = self.connect_to_player_data() # Connect to
        if not self.__ready:
            self.setup_player_tables(player_data_dictionary)
        cursor = connection.cursor() # Create cursor for the database
        cursor.execute(f'SELECT COUNT(*) FROM players WHERE username = "{player_data_dictionary['username']}"')
        user_exists = cursor.fetchone()[0] > 0
        if user_exists:
            cursor.execute(f'SELECT id FROM players where username = "{player_data_dictionary['username']}"')
            player_id = cursor.fetchone()[0]
            for key, value in player_data_dictionary.items():
                if key == 'is_alive':
                    cursor.execute(f'SELECT is_alive FROM player_data WHERE player_id = {player_id}')
                    if cursor.fetchone()[0] != value and value == False: # Death detected
                        cursor.execute(f'SELECT COUNT(*) FROM player_deaths WHERE player_id = {player_id} AND timestamp = {player_data_dictionary['timestamp']}')
                        if not cursor.fetchone()[0] > 0: # Verify the death isn't already recorded
                            cursor.execute(f'INSERT INTO player_deaths (player_id, timestamp, player_data) VALUES (?, ?, ?)', (player_id, player_data_dictionary['timestamp'], json.dumps(player_data_dictionary)))
                            changes.append(('death', 1, value))
                elif key == 'coords':
                    cursor.execute(f'UPDATE coords SET x = {value['x']} WHERE player_id = {player_id}')
                    cursor.execute(f'UPDATE coords SET y = {value['y']} WHERE player_id = {player_id}')
                    cursor.execute(f'UPDATE coords SET z = {value['z']} WHERE player_id = {player_id}')
                elif key == 'nutrition':
                    cursor.execute(f'UPDATE nutrition SET weight = {value['weight']} WHERE player_id = {player_id}')
                    cursor.execute(f'UPDATE nutrition SET calories = {value['calories']} WHERE player_id = {player_id}')
                    cursor.execute(f'UPDATE nutrition SET carbohydrates = {value['carbohydrates']} WHERE player_id = {player_id}')
                    cursor.execute(f'UPDATE nutrition SET proteins = {value['proteins']} WHERE player_id = {player_id}')
                    cursor.execute(f'UPDATE nutrition SET lipids = {value['lipids']} WHERE player_id = {player_id}')
                elif key == 'perks':
                    for perk in value.keys():
                        cursor.execute(f'SELECT "{perk}" FROM perks WHERE player_id = {player_id}')
                        current_value = cursor.fetchone()[0]
                        if current_value != value[perk]:
                            changes.append(('perks', perk, current_value, value[perk]))
                            cursor.execute(f'UPDATE perks SET "{perk}" = {value[perk]} WHERE player_id = {player_id}')
                elif key == 'traits': # WIP
                    for trait in value:
                        trait_string = f'"{trait}"'
                        cursor.execute('SELECT COUNT(*) FROM traits WHERE trait = ?', (trait_string, ))
                        trait_exists = cursor.fetchone()[0] > 0
                        if not trait_exists:
                            cursor.execute('INSERT INTO traits (trait) VALUES (?)', (trait_string, ))
                        cursor.execute('SELECT id FROM traits WHERE trait = ?', (trait_string, ))
                        trait_id = cursor.fetchone()[0]
                        cursor.execute('SELECT COUNT(*) FROM player_traits WHERE player_id = ? AND trait_id = ?', (player_id, trait_id))
                        player_trait_connection = cursor.fetchone()[0]
                        if not player_trait_connection:
                            cursor.execute('INSERT INTO player_traits (player_id, trait_id) VALUES (?, ?)', (player_id, trait_id))
                elif key == 'timestamp':
                    cursor.execute(f'UPDATE players SET last_updated = {value} WHERE id = {player_id}')
                else:
                    cursor.execute(f'SELECT {key} FROM player_data WHERE player_id = {player_id}')
                    current_value = cursor.fetchone()[0]
                    if current_value != value:
                        changes.append((key, current_value, value))
                        cursor.execute(f'UPDATE player_data SET {key} = {value} WHERE player_id = {player_id}')
            # player_data

            # coords

            # nutrition

            # perks
            # cursor.execute(f'''UPDATE players SET ''')
            # for perk, value in player_data_dictionary['perks'].items():
            #     cursor.execute(f'UPDATE perks SET "{perk}" = {value}')

            # traits

            
            connection.commit()
            connection.close()
            # print(f'Updated {player_data_dictionary['username']} in the database.')
        else:
            cursor.execute('INSERT INTO players (username, created, last_updated) VALUES (?, ?, ?)',
                           (player_data_dictionary['username'],
                           player_data_dictionary['timestamp'],
                           player_data_dictionary['timestamp']))
            cursor.execute(f'SELECT id FROM players WHERE username = "{player_data_dictionary['username']}"')
            player_id = cursor.fetchone()[0]
            cursor.execute('''
INSERT INTO player_data (
                           player_id,
                           steam_id,
                           server_user_id,
                           username,

                           ping,
                           display_name,
                           character_name,
                           access_level,

                           role,
                           faction,
                           is_alive,
                           profession,

                           time_survived_float,
                           time_survived_string,
                           zombie_kills,
                           survivor_kills

                           ) VALUES (
                           ?, ?, ?, ?, 
                           ?, ?, ?, ?, 
                           ?, ?, ?, ?, 
                           ?, ?, ?, ?
                           )''', (
                               player_id,
                               player_data_dictionary['steam_id'],
                               player_data_dictionary['server_user_id'],
                               player_data_dictionary['username'],

                               player_data_dictionary['ping'],
                               player_data_dictionary['display_name'],
                               player_data_dictionary['character_name'],
                               player_data_dictionary['access_level'],

                               player_data_dictionary['role'],
                               player_data_dictionary['faction'],
                               player_data_dictionary['is_alive'],
                               player_data_dictionary['profession'],

                               player_data_dictionary['time_survived_float'],
                               player_data_dictionary['time_survived_string'],
                               player_data_dictionary['zombie_kills'],
                               player_data_dictionary['survivor_kills'],
                           ))
            cursor.execute('INSERT INTO coords (player_id, x, y, z) VALUES (?, ?, ?, ?)', (
                player_id, 
                player_data_dictionary['coords']['x'],
                player_data_dictionary['coords']['y'],
                player_data_dictionary['coords']['z'],
            ))
            cursor.execute('INSERT INTO nutrition (player_id, weight, calories, carbohydrates, proteins, lipids) VALUES (?, ?, ?, ?, ?, ?)', (
                player_id,
                player_data_dictionary['nutrition']['weight'],
                player_data_dictionary['nutrition']['calories'],
                player_data_dictionary['nutrition']['carbohydrates'],
                player_data_dictionary['nutrition']['proteins'],
                player_data_dictionary['nutrition']['lipids'],
            ))
            perkList = []
            perkListValues = []
            for perk in player_data_dictionary['perks']:
                perkList.append(f'"{perk}"')
                perkListValues.append(player_data_dictionary['perks'][perk])
            placeholders = ', '.join(['?']*len(perkList))
            cursor.execute(f'INSERT INTO perks (player_id, {', '.join(perkList)}) VALUES (?, {placeholders})', 
                (player_id, ) + tuple(perkListValues)
                )

            for trait in player_data_dictionary['traits']:
                trait_string = f'"{trait}"'
                cursor.execute('SELECT COUNT(*) FROM traits WHERE trait = ?', (trait_string, ))
                trait_exists = cursor.fetchone()[0] > 0
                if not trait_exists:
                    cursor.execute('INSERT INTO traits (trait) VALUES (?)', (trait_string, ))
                cursor.execute('SELECT id FROM traits WHERE trait = ?', (trait_string, ))
                trait_id = cursor.fetchone()[0]
                cursor.execute('INSERT INTO player_traits (player_id, trait_id) VALUES (?, ?)', (player_id, trait_id))
            changes.append(('newPlayer', player_data_dictionary['username']))
            connection.commit()
            connection.close()
            # print(f'Added {player_data_dictionary['username']} to the database.')
        return changes
    # end update_player

#     def setup_databases(self, player_data_dictionary) -> None:
#         if not Path(self.__database_path).is_dir(): # Create local player data directory if it doesn't exist
#             Path(self.__database_path).mkdir()

#         connection = self.connect_to_player_data()
#         res = connection.cursor().execute("SELECt name FROM sqlite_master")
#         tables = []
#         notNone = True
#         while notNone:
#             temp = res.fetchone()
#             if temp != None:
#                 tables.append(temp[0])
#             else:
#                 notNone = False
#         if "player_data" not in tables:
#             player_data_execute_string = [
#                 "CREATE TABLE player_data ( username VARCHAR PRIMARY KEY,",
#                 "steam_id INTEGER,",
#                 "server_user_id INTEGER,",
#                 "ping INTEGER,",
#                 "displa_name VARCHAR,",
#                 "character_name VARCHAR,",
#                 "access_level VARCHAR,",
#                 "role VARCHAR,",
#                 "faction VARCHAR,",
#                 "is_alive INTEGER,",
#                 "profession VARCHAR,",
#                 "time_survived_float REAL,",
#                 "time_survived_string VARCHAR,",
#                 "zombie_kills INTEGER,",
#                 "survivor_kills INTEGER,",

#                 # COORDS
#                 "x REAL,",
#                 "y REAL,",
#                 "z REAL,",

#                 # NUTRITION
#                 "weight INT,",
#                 "calories REAL,",
#                 "carbohydrates REAL,",
#                 "proteins REAL,",
#                 "lipids REAL,",
#                 ")"
#             ]
#             connection.cursor().execute(" ".join(player_data_execute_string))
#         # if "coords" not in tables:
#         #     connection.cursor().execute("CREATE TABLE coords (username VARCHAR PRIMARY KEY, x REAL, y REAL, z REAL)")
#         # if "nutrition" not in tables:
#         #     connection.cursor().execute("CREATE TABLE nutrition (username VARCHAR PRIMARY KEY, weight INT, calories REAL, carbohydrates REAL, proteins REAL, lipids REAL)")
#         if "perks" not in tables: # Requires an initial list of perks (to keep it dynamic according to the user's perk list)
#             perk_execute_string = ["CREATE TABLE perks ( username VARCHAR PRIMARYU KEY,",]
#             for perk in player_data_dictionary['perks']:
#                 perk_execute_string.append(f"{perk} INT")
#             perk_execute_string.append(")")
#             connection.cursor().execute(" ".join(perk_execute_string))
#         if "traits" not in tables: # Composite Primary Key: (username VARCHAR, trait VARCHAR(100) PRIMARY KEY)
#             # Alternatively have two tables here, one that is just traits, then one that utilizing the composite primary key as the key and then 
#             # referencing both player usernames from the main table and traits names from the trait table
#             connection.cursor().execute("CREATE TABLE traits (trait VARCHAR(100) PRIMARY KEY)")
#             # Create link table
#             connection.cursor().execute("CREATE TABLE playerTraits ((username, trait) PRIMARY KEY, FOREIGN KEY username REFERENCES player_data(username), FOREIGN KEY trait REFERENCES traits(trait), username VARCHAR, trait VARCHAR(100))")
#         if "timestamps" not in tables:
#             connection.cursor().execute("CREATE TABLE timestamps (username VARCHAR PRIMARY KEY, timestamp REAL)")
#         if "deaths" not in tables:
#             connection.cursor().execute("CREATE TABLE deaths (username VARCHAR PRIMARY KEY, timestamp REAL, death BLOB)")
#         connection.commit()
#         connection.close()
#     # end setup_databases

#     # def update_player_data(self, player_data_dictionary) -> list:
#     #     # Returns a list of everything that has changed 
#     #     if not self.__database_setup:
#     #         self.setup_databases(player_data_dictionary)
#     #     if self.check_if_username_exists("player_data", player_data_dictionary['username']):
#     #         changes = []
#     #         for key, value in player_data_dictionary:
#     #             if key == "perks":
#     #                 for perk, level in player_data_dictionary[key]:
#     #                     prev = self.get_from("player_data", player_data_dictionary['username'], perk) # Revisit this logic
#     #                     if value != prev:
#     #                         changes.append(('perks', key, value, prev,))
#     #                         self.update_one_in_player_data(player_data_dictionary['username'], key, value)
#     #             elif key == "traits":
#     #                 pass
#     #             else:
#     #                 pass
#     #         return changes
#     #     return []
#     # # end update_player_data

#     def check_if_username_exists(self, table:str, username:str) -> bool:
#         connection = self.connect_to_player_data()
#         res = connection.cursor().execute(f"SELECT username FROM {table} WHERE username=\"{username}\"")
#         if res.fetchone():
#             connection.close()
#             return True
#         else:
#             connection.close()
#             return False
#     # end check_if_username_exists

#     def update_one_in_player_data(self, username:str, columnName:str, value:str) -> bool:
#         success = False
#         connection = self.connect_to_player_data()
#         input = f"UPDATE \"player_data\" SET {columnName} = {value} WHERE username = \"{username}"
#         res = connection.cursor().execute(input)
#         if res.rowcount > 0:
#             success = True
#         connection.commit()
#         connection.close()
#         return success
#     # end update_one_in

#     def insert_into(self, table:str, *args:str, **kwargs) -> bool:
#         newKwargs = []
#         for arg in args:
#             if arg in kwargs:
#                 if isinstance(kwargs[arg], str):
#                     newKwargs.append(f"\"{str(kwargs[arg])}\"")
#                 else:
#                     newKwargs.append(str(kwargs[arg]))
#         connection = self.connect_to_player_data()
#         # kwargs and args needs to be sync'd up somehow, perhaps converting kwargs into a list would be ideal
#         if self.check_if_username_exists(table, kwargs["username"]):
#             updates = []
#             for index, arg in enumerate(args):
#                 updates.append(f"{arg} = {newKwargs[index]}")
#             input = f"UPDATE {table} SET {", ".join(updates)} WHERE username = \"{kwargs["username"]}\";"
#             # print(input)
#             res = connection.cursor().execute(input)
#         else:
#             input = f"INSERT INTO {table} ({", ".join(args)}) VALUES ({", ".join(newKwargs)});"
#             # print(input)
#             res = connection.cursor().execute(input)
#         connection.commit()
#         connection.close()
#         return True
#     # end insert_into

#     def get_all_usernames(self, table:str) -> list[str]:
#         connection = self.connect_to_player_data()
#         res = connection.cursor().execute(f"SELECT username FROM {table}")
#         result = res.fetchall()
#         connection.close()
#         players = []
#         for player in result:
#             players.append(player[0])
#         return players
#     # end get_all_usernames

#     def get_from(self, table:str, username:str, *args:str) -> dict: # WIP
#         resulting_dict = {}
#         connection = self.connect_to_player_data()
#         # print(args)
#         if args:
#             res = connection.cursor().execute(f"SELECT {", ".join(args)} FROM {table}")
#             result = res.fetchall()
#             for index, arg in enumerate(args):
#                 resulting_dict[arg] = result[0][index]
#             if 'username' not in resulting_dict:
#                 resulting_dict['username'] = username
#         else:
#             res = connection.cursor().execute(f"SELECT name FROM pragma_table_info('{table}');")
#             column_names = []
#             result = res.fetchall()
#             for i in result:
#                 column_names.append(i[0])
#             # print(column_names)
#             res = connection.cursor().execute(f"SELECT * FROM {table} WHERE username = \"{username}\"")
#             result = res.fetchall()
#             for i in result:
#                 for index, name in enumerate(column_names):
#                     resulting_dict[name] = i[index]
#         return resulting_dict
#     # end get_from

#     def get_players_with(self, table:str, column_name:str, value) -> list[str]:
#         # Returns list of players where the given column_name is equal to the requested value
#         return ['']
#     # end get_from
# # end Agent_Database

# if __name__ == "__main__":
#     newDB = Agent_Database()
#     newDB.setup_databases({"perks" : {"axe" : 1,}})
#     # print(newDB.check_if_username_exists(table="coords", username="ComradeWolf"))
#     newDB.insert_into("coords", "username", "x", "y", "z", username="ComradeWolf", x=7, y=66, z=1)
#     newDB.insert_into("coords", "username", "x", "y", "z", username="Pedguin", x=7, y=66, z=1)
#     newDB.insert_into("coords", "username", "x", "y", "z", username="Osie", x=7, y=66, z=1)
#     newDB.insert_into("coords", "username", "x", "y", "z", username="Hestefyr", x=7, y=66, z=1)
#     newDB.insert_into("coords", "username", "x", "y", "z", username="Dawn", x=7, y=66, z=1)
#     newDB.insert_into("coords", "username", "x", "y", "z", username="Cyol", x=7, y=66, z=1)
#     print(newDB.get_all_usernames("coords"))
#     print(newDB.get_from("coords", "Cyol"))

#     # newDB.get_from("coords", )