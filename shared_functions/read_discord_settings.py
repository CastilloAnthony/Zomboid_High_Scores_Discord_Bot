# Developed by Anthony Castillo (ComradeWolf) for Peter Mann (Pedguin)
# Last Update: 04/05/2026 (DD/MM/YYYY)

import json
from pathlib import Path
import logging
LOGGER: logging.Logger = logging.getLogger("bot")

def read_discord_settings(file_path = './settings_discord.json') -> dict:
    if not Path(file_path).is_file():     
        with open(file_path, 'w') as file:     
            json.dump({ 
                "pedguinBot" : {
                    "botToken" : "",
                    "client-ID" : "",
                    "public-ID" : "",
                    "secret-ID" : "",
                    "redirect-URL" : "https://discord.com/api/oauth2/authorize?client_id=825455539399557181&permissions=8&redirect_uri=https%3A%2F%2Fdiscord.com%2Fapi%2Foauth2%2Fauthorize%3Fclient_id%3D825455",
                    "redirect-URL2" : "",
                    "ANNOUNCE_CHANNEL_ID" : 0,
                    "LEVELUP_CHANNEL_ID" : 0, 
                    "GUILD_ID" : 0 
                }}, file, indent=4) # Redirect URLS are not really needed here.
        LOGGER.info('Created new settings_discord.json file, please fill out missing passwords and/or incorrect and/or missing data.')
        input('Press Enter to continue...')
        with open(file_path, 'r') as file:
            return json.load(file)
    else:
        with open(file_path, 'r') as file:
            return json.load(file)
# end read_discord_settings