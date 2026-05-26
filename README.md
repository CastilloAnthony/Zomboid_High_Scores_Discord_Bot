# Zomboid High Scores Discord Bot
## Developed by Anthony Castillo (ComradeWolf) for Peter Mann (Pedguin)
### Last Update: 04/05/2026 (DD/MM/YYYY)

A personalized discord bot made using the discord 2.6.4 library alongside the mcrcon 0.7.0 library for direct interactions with the Project Zomboid server and the paramiko 4.0.0 library for communicating with the host of the server. Includes custom slash prefixed commands, logging, and files for inputting your own authentication information.

### QuickStart:
0. Subscribe to the companion mod Player Character Data Collector for a project zomboid server: https://steamcommunity.com/sharedfiles/filedetails/?id=3673637678
1. Install requirements.txt using pipreqs (pip install -r requirements.txt)
2. Launch bot.py
3. Fill out the newly created settings_connection.json and settings_discord.json with your appropriate information.
4. Relaunch bot.py
5. You should now be able to interact with the bot in discord channels. Try the '/commands' or '/help' command.

#### Todo (High priority at top, low priority at bottom):
- Have the bot's login messages appear in-game as well as in discord (Requires a new game mod?)
- Modify agent_player_data's poll_player_data function to only attempt to copy files that are different than what is stored locally (compare by byte size?)
- Reimplement data storage method as database instead of json file
- Implement pz-to-discord connection (whitelisting system? claiming system? ticketing system?)
- Remove anomalous player data (ongoing as they appear)
- Twitch bot to say deaths in twitch chat (very low priority, and possibly never)