import os
from pathlib import Path
import asyncio
import json
import aiosqlite

class Database_Player_Deaths():
    def __init__(self, database_path='./data/', database_name='player_deaths.db') -> None:
        self.__database_path = database_path
        self.__database_name = database_name
        self.__database_location = os.path.join(self.__database_path, self.__database_name)
        self.__usernames = []
        if not asyncio.run(self._verify_database()):
            asyncio.run(self._setup_database())
        # asyncio.run(self.read_usernames())
    # end __init__

    async def _verify_database(self) -> bool:
        if not Path(self.__database_path).is_dir():
            Path(self.__database_path).mkdir()
        if Path(self.__database_location).is_file():
            return True
        return False
    # end _verify_database

    async def _setup_database(self) -> None:
        async with aiosqlite.connect(self.__database_location) as db:
            await db.execute('''
            CREATE TABLE IF NOT EXISTS player_deaths (
                       death_id INTEGER,
                       username VARCHAR NOT NULL,
                       timestamp REAL NOT NULL,
                       player_data BLOB,
                       PRIMARY KEY (username, timestamp)
                       )''')
            await db.commit()
    # end _setup_database

    async def read_usernames(self) -> None:
        async with aiosqlite.connect(self.__database_location) as db:
            async with db.execute('SELECT username FROM player_deaths') as cursor:
                async for row in cursor:
                    if row[0] not in self.__usernames:
                        self.__usernames.append(row[0])
    # end read_usernames

    async def add_death(self, username:str, timestamp:float, player_dict:dict) -> None:
        async with aiosqlite.connect(self.__database_location) as db:
            async with db.execute('SELECT username, timestamp, player_data FROM player_deaths WHERE username = ? AND timestamp = ?', (username, timestamp,)) as cursor:
                async for row in cursor:
                    if row[0] == username and row[1] == timestamp:
                        return
            await db.execute('INSERT INTO player_deaths (death_id, username, timestamp, player_data) VALUES ((SELECT IFNULL(MAX(death_id) + 1, 0) FROM player_deaths), ?, ?, ?)', (username, timestamp, json.dumps(player_dict)))
            await db.commit()
            if username not in self.__usernames:
                self.__usernames.append(username)
    # end add_death
        
    async def get_death(self, death_id:int) -> dict:
        async with aiosqlite.connect(self.__database_location) as db:
            async with db.execute('SELECT death_id, player_data FROM player_deaths WHERE death_id = ?', (death_id,)) as cursor:
                async for row in cursor:
                    if row[0] == death_id:
                        return json.loads(row[1])
        return {}
    # end retrieve_death

    async def get_list_of_deaths(self, username:str = '', quantity:int = 10) -> list[tuple[int, float, str]]:
        player_deaths = []
        async with aiosqlite.connect(self.__database_location) as db:
            if username != '':
                async with db.execute('SELECT death_id, timestamp, username FROM player_deaths WHERE username = ? ORDER BY death_id DESC LIMIT ?', (username, quantity)) as cursor:
                    async for row in cursor:
                        player_deaths.append((row[0], row[1], row[2]))
            else:
                async with db.execute('SELECT death_id, timestamp, username FROM player_deaths ORDER BY death_id DESC LIMIT ?', (quantity,)) as cursor:
                    async for row in cursor:
                        player_deaths.append((row[0], row[1], row[2]))
        return player_deaths
    # end get_deaths_list

    async def get_list_around(self, death_id, radius:int=5) -> list[tuple[int, float, str]]:
        player_deaths = []
        async with aiosqlite.connect(self.__database_location) as db:
            async with db.execute('SELECT death_id, timestamp, username FROM player_deaths WHERE death_id >= ? - ? AND death_id <= ? + ? ORDER BY death_id DESC', (death_id, radius, death_id, radius,)) as cursor:
                async for row in cursor:
                    player_deaths.append((row[0], row[1], row[2]))
        return player_deaths
    # end get_list_around

    async def get_list_usernames(self) -> list[str]:
        return self.__usernames
    # end get_list_usernames
# end Database_Player_Deaths