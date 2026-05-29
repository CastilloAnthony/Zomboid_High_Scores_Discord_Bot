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
        if not asyncio.run(self._verify_database()):
            asyncio.run(self._setup_database())
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
                       username VARCHAR NOT NULL,
                       timestamp REAL NOT NULL,
                       player_data BLOB,
                       PRIMARY KEY (username, timestamp)
                       )''')
            await db.commit()
    # end _setup_database

    async def add_death(self, username:str, timestamp:float, player_dict:dict) -> None:
        async with aiosqlite.connect(self.__database_location) as db:
            async with db.execute('SELECT username, timestamp, player_data FROM player_deaths WHERE username = ? AND timestamp = ?', (username, timestamp,)) as cursor:
                async for row in cursor:
                    if row[0] == username and row[1] == timestamp:
                        return
            await db.execute('INSERT INTO player_deaths (username, timestamp, player_data) VALUES (?, ?, ?)', (username, timestamp, json.dumps(player_dict)))
            await db.commit()
    # end add_death
        
    async def retrieve_death(self, username:str, timestamp:float) -> dict:
        async with aiosqlite.connect(self.__database_location) as db:
            async with db.execute('SELECT username, timestamp, player_data FROM player_deaths WHERE username = ? AND timestamp = ?', (username, timestamp,)) as cursor:
                async for row in cursor:
                    if row[0] == username and row[1] == timestamp:
                        return json.loads(row[2])
        return {}
    # end retrieve_death

    async def get_deaths_list(self, username:str = '') -> list[tuple[float, str]]:
        player_deaths = []
        async with aiosqlite.connect(self.__database_location) as db:
            if username != '':
                async with db.execute('SELECT timestamp, username FROM player_deaths WHERE username = ?', (username,)) as cursor:
                    async for row in cursor:
                        player_deaths.append((row[0], row[1]))
            else:
                async with db.execute('SELECT timestamp, username FROM player_deaths') as cursor:
                    async for row in cursor:
                        player_deaths.append((row[0], row[1]))
        return player_deaths
    # end get_deaths_list