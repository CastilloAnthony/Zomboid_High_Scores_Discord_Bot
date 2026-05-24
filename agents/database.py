# Developed by Anthony Castillo (ComradeWolf) for Peter Mann (Pedguin)
# Last Update: 04/05/2026 (DD/MM/YYYY)

import os
from pathlib import Path
import sqlite3
import json
class Agent_Player_Database():
    def __init__(self, database_name:str = 'player_data.db', database_path:str = './data'):
        """Initializes the database.

        Args:
            database_name (str, optional): The name of the database. Defaults to 'player_data.db'.
            database_path (str, optional): The path to where the database will be saved. Defaults to './data'.
        """
        self.__database_path = database_path
        self.__database_name = database_name
        # self.__table_names = ['players', 'coords', 'nutrition', 'traits', 'player_traits', 'player_info', 'player_deaths', 'perks']
        self.__ready = False
        self.check_for_databases()
        self._setup_basic_tables()
        # self.setup_databases()
    # end __init__
    
    def _connect_to_player_data(self) -> sqlite3.Connection:
        """Returns a connection to the database.

        Returns:
            sqlite3.Connection: A connection to the database.
        """
        return sqlite3.connect(os.path.join(self.__database_path, self.__database_name))
    # end _connect_to_player_data

    def check_for_databases(self) -> None:
        """Creates the local directory that the database will be saved in if it doesn't already exist.
        """
        if not Path(self.__database_path).is_dir(): # Create local player data directory if it doesn't exist
            Path(self.__database_path).mkdir()
    # end check_for_databases

    def _setup_basic_tables(self) -> None:
        """Creates the database and the table schemes if they do not already exist.
        """
        connection = self._connect_to_player_data()
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
                            total_play_time REAL,
                            last_login REAL
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
    # end _setup_basic_tables

    def _setup_perk_table(self, player_data_dictionary:dict) -> None:
        """Dynamically creates the perks table, based on the inputted dictionary, if it doesn't already exist.

        Args:
            player_data_dictionary (dict): A player's character data.
        """
        connection = self._connect_to_player_data()
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
    # end _setup_perk_table

    def update_player(self, player_data_dictionary:dict) -> list[tuple[str, str | int | float, str | int | float, int | None]]: # Update the player data for a given player_id
        """Updates a player's entries in the database according to the input dictionary.

        Args:
            player_data_dictionary (dict): A player's character data.

        Returns:
            list[tuple]: A list of tuples denoting the changes that were made. [('column', prevValue, newValue), ...]
        """
        changes = []
        connection = self._connect_to_player_data() # Connect to
        if not self.__ready:
            self._setup_perk_table(player_data_dictionary)
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
                    cursor.execute('SELECT trait_id FROM player_traits WHERE player_id = ?', (player_id,))
                    trait_ids = [trait_id[0] for trait_id in cursor.fetchall()]
                    traits_player_had = []
                    for trait_id in trait_ids: # Getting all current traits
                        cursor.execute('SELECT trait FROM traits WHERE trait_id = ?', (trait_id,))
                        traits_player_had.append(cursor.fetchone()[0])
                    for trait in value: # Adding new traits
                        if trait in traits_player_had: # Removing traits that will remain unchanged in the database
                            traits_player_had.remove(trait)
                        trait_string = f'{trait}'
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
                            changes.append(('trait', 'gain', trait))
                    for trait in traits_player_had: # Removing old traits
                        cursor.execute('SELECT trait_id FROM traits WHERE trait = ?', (trait,))
                        trait_id = cursor.fetchone()[0]
                        cursor.execute('DELETE FROM player_traits WHERE player_id = ? AND trait_id = ?', (player_id, trait_id))
                        changes.append(('trait', 'lost', trait))
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
                           0, 0))
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

    def _get_column_names(self, table:str) -> list[str]:
        """Retrieves a list of all columns from a given table.

        Args:
            table (str): The name of a table

        Returns:
            list[str]: A list of column names.
        """
        column_names = []
        connection = self._connect_to_player_data() # Connect to
        cursor = connection.cursor() # Create cursor for the database
        cursor.execute(f'PRAGMA table_info({table})')
        columns = cursor.fetchall()
        column_names = [info[1] for info in columns]
        connection.close()
        return column_names
    # end _get_column_names
    
    def get_all_usernames(self) -> list[str]:
        """Retrieves a list of all usernames from the database.

        Returns:
            list[str]: A list of usernames.
        """
        usernames = []
        connection = self._connect_to_player_data() # Connect to
        cursor = connection.cursor() # Create cursor for the database
        cursor.execute('SELECT username FROM players')
        usernames = [user[0] for user in cursor.fetchall()]
        connection.close()
        return usernames
    # end get_all_usernames

    def get_all_nutrition_columns(self) -> list[str]:
        """Retrieves a list of all column names from the nutrition table.

        Returns:
            list[str]: A list of all column names in the nutrition table.
        """
        return self._get_column_names('nutrition')[1:]
    # end get_all_nutrition_columns

    def get_all_perks(self) -> list:
        return self._get_column_names('perks')[1:]
    # end get_all_perks

    def get_all_traits(self) -> list[str]:
        """Retrieves a list of all unique traits that the database has seen and recorded. 

        Returns:
            list[str]: A list of all traits recorded in the database.
        """
        traits = []
        connection = self._connect_to_player_data() # Connect to
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
        connection = self._connect_to_player_data() # Connect to
        cursor = connection.cursor() # Create cursor for the database
        cursor.execute('SELECT id FROM players WHERE username = ?', (username,))
        player_id = cursor.fetchone()[0]
        player_data_columns = self._get_column_names('player_data')
        cursor.execute('SELECT * FROM player_data WHERE player_id = ?', (player_id,))
        player_data = cursor.fetchall()[0]
        for key, value in enumerate(player_data_columns):
            player_data_dict[value] = player_data[key]
        
        player_data_dict['coords'] = {}
        cursor.execute('SELECT * FROM coords WHERE player_id = ?', (player_id,))
        coords = cursor.fetchall()[0]
        coords_columns = self._get_column_names('coords')
        for key, value in enumerate(coords_columns[1:]):
            player_data_dict['coords'][value] = coords[key]

        player_data_dict['nutrition'] = {}
        cursor.execute('SELECT * FROM nutrition WHERE player_id = ?', (player_id,))
        nutrition = cursor.fetchall()[0]
        nutrition_columns = self._get_column_names('nutrition')
        for key, value in enumerate(nutrition_columns[1:]):
            player_data_dict['nutrition'][value] = nutrition[key]

        player_data_dict['perks'] = {}
        cursor.execute('SELECT * FROM perks WHERE player_id = ?', (player_id,))
        perks = cursor.fetchall()[0]
        perks_columns = self._get_column_names('perks')
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
    
    def get_usernames_with(self, column_name:str, value) -> list[str]:
        """Retrieves a list of all usernames that have a specific value in a specific column.

        Args:
            column_name (str): The column name to match with.
            value (_type_): The value to match with.

        Returns:
            list[str]: A list of usernames.
        """
        players = []
        connection = self._connect_to_player_data() # Connect to
        cursor = connection.cursor() # Create cursor for the database
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
        tables = cursor.fetchall()
        acquired_table_name = ''
        if not column_name  == 'trait':
            for table_name in [table[0] for table in tables]:
                for column in self._get_column_names(table_name):
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

    def get_player_last_updated_timestamp(self, username:str = '') -> list[tuple[str, float]]:
        """Retrieves a list of username-timestamp tuples from the database. The timestamp represents the time at which the user was
            last updated in the database. If username is not left at default then the list will only have one tuple in it, otherwise
            it retrieves all player username-timestamps.

        Args:
            username (str, optional): The name of the user to retrieve the timestamp from. Defaults to ''.

        Returns:
            list[tuple[str, float]]: A list of tuples with the format of (username, timestamp).
        """
        players_last_updated_timestamps = []
        connection = self._connect_to_player_data() # Connect to
        cursor = connection.cursor() # Create cursor for the database
        if username == '':
            cursor.execute('SELECT username, last_updated FROM players')
            players_last_updated_timestamps = [(user[0], user[1],) for user in cursor.fetchall()]
        else:
            cursor.execute('SELECT username, last_updated FROM players WHERE username = ?', (username,))
            players_last_updated_timestamps = [(username, cursor.fetchone())]
        connection.close()
        return players_last_updated_timestamps
    # end get_player_last_updated_timestamp

    def get_player_creation_timestamp(self, username:str = '') -> list[tuple[str, float]]:
        """Retrieves a list of username-timestamp tuples from the database. The timestamp represents the time at which the user was
            first added to the database. If username is not left at default then the list will only have one tuple in it, 
            otherwise it retrieves all player username-timestamps.

        Args:
            username (str, optional):  The name of the user to retrieve the timestamp from. Defaults to ''.

        Returns:
            list[tuple[str, float]]: A list of tuples with the format of (username, timestamp).
        """
        players_creation_timestamps = []
        connection = self._connect_to_player_data() # Connect to
        cursor = connection.cursor() # Create cursor for the database
        if username == '':
            cursor.execute('SELECT username, created FROM players')
            players_creation_timestamps = [(user[0], user[1],) for user in cursor.fetchall()]
        else:
            cursor.execute('SELECT username, created FROM players WHERE username = ?', (username,))
            players_creation_timestamps = [(username, cursor.fetchone())]
        connection.close()
        return players_creation_timestamps
    # end get_player_creation_timestamp

    def get_player_total_playtime(self, username:str) -> list[tuple[str, float]]:
        """Retrieves list with just one tuple with the username and their total playtime.

        Args:
            username (str): The name of the user to retrieve the total playtime of. 

        Returns:
            list[tuple[str, float]]: A list of tuples with the format of (username, timestamp).
        """
        players_total_playtime = []
        connection = self._connect_to_player_data() # Connect to
        cursor = connection.cursor() # Create cursor for the database
        cursor.execute('SELECT total_play_time FROM players WHERE username = ?', (username,))
        players_total_playtime.append((username, cursor.fetchone()[0]))
        connection.close()
        return players_total_playtime
    # end get_player_total_playtime

    def get_player_last_login(self, username:str) -> list[tuple[str, float]]:
        player_last_login = []
        connection = self._connect_to_player_data() # Connect to
        cursor = connection.cursor() # Create cursor for the database
        cursor.execute('SELECT last_login FROM players WHERE username = ?', (username,))
        player_last_login.append((username, cursor.fetchone()[0]))
        connection.close()
        return player_last_login
    # end get_playeR_last_login

    def update_player_total_play_time(self, username:str, incrementBy:float) -> None:
        """Increments the total play time of a player stored in the database.

        Args:
            username (str): The username of the player to change.
            incrementBy (float): The number to change the total play time by. (in seconds)
        """
        connection = self._connect_to_player_data() # Connect to
        cursor = connection.cursor() # Create cursor for the database
        cursor.execute('SELECT total_play_time FROM players WHERE username = ?', (username,))
        result = cursor.fetchone()[0]
        cursor.execute(f'UPDATE players SET total_play_time = {result+incrementBy} WHERE username = {username}')
        connection.commit()
        connection.close()
    # end update_player_total_play_time

    def update_player_last_login(self, username:str, timestamp:float) -> None:
        """Sets the given user's last login time to the timestamp provided.

        Args:
            username (str): The username of the player to change.
            timestamp (float): The timestamp to set the user's last login time to.
        """
        connection = self._connect_to_player_data() # Connect to
        cursor = connection.cursor() # Create cursor for the database
        cursor.execute(f'UPDATE players SET last_login = {timestamp} WHERE username = {username}')
        connection.commit()
        connection.close()
    # end update_player_last_login

    def get_top_in(self, column_name:str, quantity:int = 10, descending=True) -> list[tuple[str, int | float]]:
        """Retrieves a truncated list of players in a specific category from the database.

        Args:
            column_name (str): The specificed category to get the top players in.
            quantity (int, optional): The amount of users to truncate up to. Defaults to 10.
            descending (bool, optional): Denotes whether to retrieve data in descending or ascending order. Defaults to True.

        Returns:
            list[tuple[str, int | float]]: a list of tuples of the format (username, value) where value is the player's value in the requested category
        """
        players_in = []
        connection = self._connect_to_player_data() # Connect to
        cursor = connection.cursor() # Create cursor for the database
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
        tables = cursor.fetchall()
        acquired_table_name = ''
        if not column_name  in [
            'trait', 'username', 'display_name', 'character_name', 'access_level', 
            'role', 'faction', 'profession', 'time_survived_string'
            ]: # Excluding columns that use strings
            for table_name in [table[0] for table in tables]:
                for column in self._get_column_names(table_name):
                    if column == column_name:
                        acquired_table_name = table_name
                        break
                if not acquired_table_name == '':
                    break
            if descending:
                cursor.execute(f'SELECT player_id, {column_name} FROM {acquired_table_name} ORDER BY {column_name} DESC')
            else:
                cursor.execute(f'SELECT player_id, {column_name} FROM {acquired_table_name} ORDER BY {column_name} ASC')
            player_ids = cursor.fetchall()
            for player_id in player_ids:
                cursor.execute('SELECT username FROM players WHERE id = ?', (player_id[0],))
                players_in.append((cursor.fetchone()[0], player_id[1]))
        connection.close()
        return players_in[:quantity]
    # end get_top_in
# end Agent_Database