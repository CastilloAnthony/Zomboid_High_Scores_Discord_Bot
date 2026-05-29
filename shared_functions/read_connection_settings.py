# Developed by Anthony Castillo (ComradeWolf) for Peter Mann (Pedguin)
# Last Update: 04/05/2026 (DD/MM/YYYY)

import json
from pathlib import Path
import logging
LOGGER: logging.Logger = logging.getLogger("bot")

def read_connection_settings(file_path = './settings_connection.json') -> dict:
    if not Path(file_path).is_file():
        with open(file_path, 'w') as file:
            json.dump({
                "RCON_HOST" : "ip.add.res.s",
                "RCON_PORT" : 0,
                "RCON_PASSWORD" : "",
                "SFTP_HOST" : "website.com",
                "SFTP_PORT" : 2022,
                "SFTP_USER" : "username.ID.etc",
                "SFTP_PASS" : "",
                "SFTP_PLAYER_DATA_PATH" : "./cache/Lua/PlayerCharacterDataCollector/Server",
                "LOCAL_PLAYER_DATA_PATH" : "./data/PlayerCharacterDataCollector",
                "POLLING_RATE" : 5,
                "MAX_POLLING_RATE" : 60,
            }, file, indent=4)
        LOGGER.info('Created new settings_connection.json file, please fill out missing passwords and/or incorrect and/or missing data.')
        input('Press Enter to continue...')
        with open(file_path, 'r') as file:
            return json.load(file)
    else:
        with open(file_path, 'r') as file:
            return json.load(file)
# end read_connection_settings