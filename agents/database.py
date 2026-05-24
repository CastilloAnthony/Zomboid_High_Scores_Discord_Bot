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
                            last_updated REAL,
                            total_play_time REAL
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
            connection.commit()
            connection.close()
        else:
            cursor.execute('INSERT INTO players (username, created, last_updated, total_play_time) VALUES (?, ?, ?, ?)',
                           (player_data_dictionary['username'],
                           player_data_dictionary['timestamp'],
                           player_data_dictionary['timestamp'],
                           0))
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
                trait_string = f'{trait}'
                cursor.execute('SELECT COUNT(*) FROM traits WHERE trait = ?', (trait_string, ))
                trait_exists = cursor.fetchone()[0] > 0
                if not trait_exists:
                    cursor.execute('INSERT INTO traits (trait) VALUES (?)', (trait_string, ))
                cursor.execute('SELECT id FROM traits WHERE trait = ?', (trait_string, ))
                trait_id = cursor.fetchone()[0]
                cursor.execute('INSERT INTO player_traits (player_id, trait_id) VALUES (?, ?)', (player_id, trait_id))

            # cursor.execute('SELECT id FROM players WHERE username = ?', (player_data_dictionary['username']))
            # player_id = cursor.fetchone()[0]
            changes.append((player_id, 'newPlayer', player_data_dictionary['username']))
            connection.commit()
            connection.close()
        return changes
    # end update_player

    def get_column_names(self, table:str) -> list:
        column_names = []
        connection = self.connect_to_player_data() # Connect to
        cursor = connection.cursor() # Create cursor for the database
        cursor.execute(f'PRAGMA table_info({table})')
        columns = cursor.fetchall()
        column_names = [info[1] for info in columns]
        connection.close()
        return column_names
    # end get_column_names
    
    def get_all_usernames(self) -> list:
        usernames = []
        connection = self.connect_to_player_data() # Connect to
        cursor = connection.cursor() # Create cursor for the database
        cursor.execute('SELECT username FROM players')
        usernames = [user[0] for user in cursor.fetchall()]
        connection.close()
        return usernames
    # end get_all_usernames

    def get_all_nutrition_columns(self) -> list:
        return self.get_column_names('nutrition')[1:]
    # end get_all_nutrition_columns

    def get_all_perks(self) -> list:
        return self.get_column_names('perks')[1:]
    # end get_all_perks

    def get_all_traits(self) -> list:
        traits = []
        connection = self.connect_to_player_data() # Connect to
        cursor = connection.cursor() # Create cursor for the database
        cursor.execute('SELECT trait FROM traits')
        traits = [trait[0] for trait in cursor.fetchall()]
        connection.close()
        return traits
    # end get_all_traits

    def get_player(self, username:str) -> dict:
        """Reconstructs the player data from the database based on username into the same dictionary format that is used when inserting the data

        Args:
            username (str): The username of the user we wish to retrieve from the database

        Returns:
            dict: The dictionary of the player data from the database in the same format it was when inserted
        """
        player_data_dict = {}
        connection = self.connect_to_player_data() # Connect to
        cursor = connection.cursor() # Create cursor for the database
        cursor.execute('SELECT id FROM players WHERE username = ?', (username,))
        player_id = cursor.fetchone()[0]
        player_data_columns = self.get_column_names('player_data')
        cursor.execute('SELECT * FROM player_data WHERE player_id = ?', (player_id,))
        player_data = cursor.fetchall()[0]
        for key, value in enumerate(player_data_columns):
            player_data_dict[value] = player_data[key]
        
        player_data_dict['coords'] = {}
        cursor.execute('SELECT * FROM coords WHERE player_id = ?', (player_id,))
        coords = cursor.fetchall()[0]
        coords_columns = self.get_column_names('coords')
        for key, value in enumerate(coords_columns[1:]):
            player_data_dict['coords'][value] = coords[key]

        player_data_dict['nutrition'] = {}
        cursor.execute('SELECT * FROM nutrition WHERE player_id = ?', (player_id,))
        nutrition = cursor.fetchall()[0]
        nutrition_columns = self.get_column_names('nutrition')
        for key, value in enumerate(nutrition_columns[1:]):
            player_data_dict['nutrition'][value] = nutrition[key]

        player_data_dict['perks'] = {}
        cursor.execute('SELECT * FROM perks WHERE player_id = ?', (player_id,))
        perks = cursor.fetchall()[0]
        perks_columns = self.get_column_names('perks')
        for key, value in enumerate(perks_columns[1:]):
            player_data_dict['perks'][value] = perks[key]

        player_data_dict['traits'] = {}
        cursor.execute('SELECT trait_id FROM player_traits WHERE player_id = ?', (player_id,))
        trait_ids = cursor.fetchall()
        traits = []
        for trait_id in trait_ids:
            cursor.execute('SELECT trait FROM traits WHERE id = ?', (trait_id))
            traits.append(cursor.fetchone()[0])
        player_data_dict['traits'] = traits

        cursor.execute('SELECT last_updated FROM players WHERE id = ?', (player_id,))
        timestamp = cursor.fetchone()[0]
        player_data_dict['timestamp'] = timestamp

        connection.close()
        return player_data_dict
    # end get_player
    
    def get_usernames_with(self, column_name:str, value) -> list:
        players = []
        connection = self.connect_to_player_data() # Connect to
        cursor = connection.cursor() # Create cursor for the database
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
        tables = cursor.fetchall()
        acquired_table_name = ''
        if not column_name  == 'trait':
            for table_name in [table[0] for table in tables]:
                for column in self.get_column_names(table_name):
                    if column == column_name:
                        acquired_table_name = table_name
                        break
                if not acquired_table_name == '':
                    break
            cursor.execute(f'SELECT player_id FROM {acquired_table_name} WHERE {column_name} = ?', (value,))
            player_ids = cursor.fetchall()
            for player_id in player_ids:
                cursor.execute('SELECT username FROM players WHERE id = ?', (player_id[0],))
                players.append(cursor.fetchone()[0])
        else:
            player_ids = []
            cursor.execute('SELECT id FROM traits WHERE trait = ?', (value,))
            trait_ids = cursor.fetchall()
            for trait_id in trait_ids:
                cursor.execute('SELECT player_id FROM player_traits WHERE trait_id = ?', (trait_id[0],))
                player_ids = cursor.fetchall()
            for player_id in player_ids:
                cursor.execute('SELECT username FROM players WHERE id = ?', (player_id[0],))
                players.append(cursor.fetchone()[0])
        connection.close()
        return players
    # end get_usernames_with

    def get_player_last_updated_timestamp(self, username:str = '') -> list:
        players_last_updated_timestamps = []
        connection = self.connect_to_player_data() # Connect to
        cursor = connection.cursor() # Create cursor for the database
        if username == '':
            cursor.execute('SELECT username, last_updated FROM players')
            players_last_updated_timestamps = [(user[0], user[1],) for user in cursor.fetchall()]
        else:
            cursor.execute('SELECT username, last_updated FROM players WHERE username = ?', (username,))
            players_last_updated_timestamps = cursor.fetchone()
        connection.close()
        return players_last_updated_timestamps
    # end get_player_last_updated_timestamp

    def get_player_creation_timestamp(self, username:str = '') -> list:
        players_creation_timestamps = []
        connection = self.connect_to_player_data() # Connect to
        cursor = connection.cursor() # Create cursor for the database
        if username == '':
            cursor.execute('SELECT username, created FROM players')
            players_creation_timestamps = [(user[0], user[1],) for user in cursor.fetchall()]
        else:
            cursor.execute('SELECT username, created FROM players WHERE username = ?', (username,))
            players_creation_timestamps = cursor.fetchone()
        connection.close()
        return players_creation_timestamps
    # end get_player_creation_timestamp

    def get_player_total_playtime(self, username:str) -> list[tuple]:
        players_total_playtime = []
        connection = self.connect_to_player_data() # Connect to
        cursor = connection.cursor() # Create cursor for the database
        cursor.execute('SELECT total_play_time FROM players WHERE username = ?', (username,))
        players_total_playtime.append((username, cursor.fetchone()[0]))
        connection.close()
        return players_total_playtime
    # end get_player_total_playtime

    def get_top_in(self, column_name:str, quantity:int = 10) -> list[tuple]:
        players_in = []
        connection = self.connect_to_player_data() # Connect to
        cursor = connection.cursor() # Create cursor for the database
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
        tables = cursor.fetchall()
        acquired_table_name = ''
        if not column_name  in [
            'trait', 'username', 'display_name', 'character_name', 'access_level', 
            'role', 'faction', 'profession', 'time_survived_string'
            ]: # Excluding columns that use strings
            for table_name in [table[0] for table in tables]:
                for column in self.get_column_names(table_name):
                    if column == column_name:
                        acquired_table_name = table_name
                        break
                if not acquired_table_name == '':
                    break
            cursor.execute(f'SELECT player_id, {column_name} FROM {acquired_table_name} ORDER BY {column_name} DESC')
            player_ids = cursor.fetchall()
            for player_id in player_ids:
                cursor.execute('SELECT username FROM players WHERE id = ?', (player_id[0],))
                players_in.append((cursor.fetchone()[0], player_id[1]))
        connection.close()
        return players_in[:quantity]
    # end get_top_in
# end Agent_Database