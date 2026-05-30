# Developed by Anthony Castillo (ComradeWolf) for Peter Mann (Pedguin)
# Last Update: 04/05/2026 (DD/MM/YYYY)

import os
import time
from pathlib import Path
import asyncio
import copy
import traceback
import paramiko
import logging
LOGGER: logging.Logger = logging.getLogger("bot")

from shared_functions.read_connection_settings import read_connection_settings
from shared_functions.player_data_functions import read_json_file, save_json_file, get_default_skills#, merge_duplicate_players
from classes.database_player_deaths import Database_Player_Deaths
class Agent_Player_Data():
    """Connects to an sftp server, copies json files from the server to a local dir, iterates over those files to import them to a variable accessible by a function
    """
    def __init__(self) -> None:
        """Imports connection settings from settings_connections.json and creates initial variable for player_data
        """
        self.__settings = read_connection_settings()
        self.__level_ups, self.__level_ups_msgs = [], []
        self.__deaths, self.__deaths_msgs = [], []
        self.__running = True
        self.__dynamic_delay = 0
        if not Path(self.__settings['LOCAL_PLAYER_DATA_PATH']).is_dir(): # Create local player data directory if it doesn't exist
            Path(self.__settings['LOCAL_PLAYER_DATA_PATH']).mkdir()
        if not Path(self.__settings['LOCAL_PLAYER_DATA_PATH']+"/Player_Data").is_dir(): # Create
            Path(self.__settings['LOCAL_PLAYER_DATA_PATH']+"/Player_Data").mkdir()
        self.__timestamps = read_json_file(os.path.join(self.__settings['LOCAL_PLAYER_DATA_PATH'], 'player_data_timestamps.json'))
        self.__world_data = read_json_file(os.path.join(self.__settings['LOCAL_PLAYER_DATA_PATH'], 'world_state.json'))
        self.__player_data = read_json_file(file_path='./player_data.json') # Reads player_data.json
        self.__player_deaths = Database_Player_Deaths()
        # self.merge_dupes()
        # self.repair_player_data()
        # self.poll_player_data()
    # end __init__

    def poll_player_data(self) -> bool:
        """Connects to and copies player_data.json files from the sftp server host

        Returns:
            bool: Success or failure
        """
        sftp = None
        transport = None
        try:
            transport = paramiko.Transport((self.__settings['SFTP_HOST'], self.__settings['SFTP_PORT']))
            transport.connect(username=self.__settings['SFTP_USER'], password=self.__settings['SFTP_PASS'])
            sftp = paramiko.SFTPClient.from_transport(transport)
            if sftp is None:
                raise Exception("Failed to create SFTP client")
            filenames = sftp.listdir(self.__settings['SFTP_PLAYER_DATA_PATH'])
            update = False
            if 'player_data_timestamps.json' in filenames:
                remote_file_path = remote_file_path = self.__settings['SFTP_PLAYER_DATA_PATH']+"/"+'player_data_timestamps.json'
                local_file_path = os.path.join(self.__settings['LOCAL_PLAYER_DATA_PATH'], 'player_data_timestamps.json')
                sftp.get(remotepath=remote_file_path, localpath=local_file_path)
                new_timestamps = read_json_file(local_file_path)
                for key, value in new_timestamps.items():
                    if key in self.__timestamps:
                        if value > self.__timestamps[key]:
                            remote_file_path = remote_file_path = self.__settings['SFTP_PLAYER_DATA_PATH']+"/Player_Data/"+key+'_data.json'
                            local_file_path = os.path.join(self.__settings['LOCAL_PLAYER_DATA_PATH'], "Player_Data", key+'_data.json')
                            sftp.get(remotepath=remote_file_path, localpath=local_file_path)
                            self.__timestamps[key] = value
                            if not update:
                                update = True
                    else:
                        remote_file_path = remote_file_path = self.__settings['SFTP_PLAYER_DATA_PATH']+"/Player_Data/"+key+'_data.json'
                        local_file_path = os.path.join(self.__settings['LOCAL_PLAYER_DATA_PATH'], "Player_Data", key+'_data.json')
                        sftp.get(remotepath=remote_file_path, localpath=local_file_path)
                        self.__timestamps[key] = value
                        if not update:
                            update = True
                self.__timestamps = new_timestamps
            if update:
                if 'world_state.json' in filenames:
                    remote_file_path = remote_file_path = self.__settings['SFTP_PLAYER_DATA_PATH']+"/"+'world_state.json'
                    local_file_path = os.path.join(self.__settings['LOCAL_PLAYER_DATA_PATH'], 'world_state.json')
                    sftp.get(remotepath=remote_file_path, localpath=local_file_path)
                if sftp:
                    sftp.close()
                    transport.close()
                self.update_world_data()
                self.update_player_data()
            else:
                if sftp:
                    sftp.close()
                    transport.close()

            # player_data_files = [f for f in filenames if f.endswith("_data.json")]
            # if player_data_files:
            #     for filename in player_data_files:
            #         remote_file_path = self.__settings['SFTP_PLAYER_DATA_PATH']+"/"+filename # Linux
            #         # remote_file_path =os.path.join(self.__settings['SFTP_PLAYER_DATA_PATH'], filename) # Windows
            #         local_file_path = os.path.join(self.__settings['LOCAL_PLAYER_DATA_PATH'], filename)
            #         sftp.get(remotepath=remote_file_path, localpath=local_file_path)
            #     if sftp:
            #         sftp.close()
            #         transport.close()
            #     self.update_player_data()

            if self.__dynamic_delay >= 5: # Decrement dynamic delay if we had a successful interaction with the server
                self.__dynamic_delay -= 5
                if self.__dynamic_delay != 0:
                    LOGGER.info(f'agent_player_data delay now set to {self.__settings['POLLING_RATE'] + self.__dynamic_delay}s')
        except:
            error = traceback.format_exc()
            lines = error.split('\n')
            print(error)
            LOGGER.error('Can\'t reach Bisect Hosting: '+str(lines[-1]))
            LOGGER.error('Error in agent_player_data.py function poll_player_data')
            if self.__dynamic_delay < (self.__settings['MAX_POLLING_RATE'] - self.__settings['POLLING_RATE']): # Increment dynamic delay if there was an error in interacting with the server
                self.__dynamic_delay += 5
                LOGGER.info(f'agent_player_data delay now set to {self.__settings['POLLING_RATE'] + self.__dynamic_delay}s')
            return False
        finally:
            if sftp:
                sftp.close()
            if transport:
                transport.close()
        return True
    # end poll_server

    def update_world_data(self) -> None:
        world_data = read_json_file(os.path.join(self.__settings['LOCAL_PLAYER_DATA_PATH'], 'world_state.json'))
        if world_data:
            if 'time' in world_data:
                self.__world_data = world_data
    # end update_world_data

    def update_player_data(self) -> None:
        """Imports json files from a specific directory into a local variable and saves an updated player_data.json
        """
        for (dir_path, dir_names, filenames) in os.walk(self.__settings['LOCAL_PLAYER_DATA_PATH']+'/Player_Data'):
            for filename in filenames:
                local_file_path = os.path.join(dir_path, filename)
                if os.path.getsize(local_file_path) != 0: # Ensures file is not empty
                    player_data = read_json_file(local_file_path)
                    if player_data: # Ensures json data is not empty
                        if not player_data['username'].isnumeric():
                            if player_data['username'] in self.__player_data:
                                if 'totalPlayTime' in self.__player_data[player_data['username']]:
                                    player_data['totalPlayTime'] = self.__player_data[player_data['username']]['totalPlayTime']
                                else:
                                    player_data['totalPlayTime'] = 0

                                if 'lastLogin' in self.__player_data[player_data['username']]:
                                    player_data['lastLogin'] = self.__player_data[player_data['username']]['lastLogin']
                                else:
                                    player_data['lastLogin'] = time.time()

                                if 'lastPoll' in self.__player_data[player_data['username']]:
                                    player_data['lastPoll'] = self.__player_data[player_data['username']]['lastPoll']
                                else:
                                    player_data['lastPoll'] = time.time()

                                if player_data['is_alive'] == self.__player_data[player_data['username']]['is_alive']: # Ensures that player is still alive and not a new character
                                    for perk in player_data['perks']:
                                        if player_data['perks'][perk] == self.__player_data[player_data['username']]['perks'][perk]+1: # Level Up Detection
                                            self.__level_ups.append((
                                                player_data['username'], # Username
                                                perk, # Name of Perk
                                                player_data['perks'][perk], # New level of perk
                                                self.__player_data[player_data['username']]['perks'][perk] # Player's previous perk level
                                                ))

                                # if 'deaths' not in player_data:
                                #     if 'deaths' in self.__player_data[player_data['username']]:
                                #         player_data['deaths'] = self.__player_data[player_data['username']]['deaths']
                                #     else:
                                #         player_data['deaths'] = []

                                if player_data['is_alive'] != self.__player_data[player_data['username']]['is_alive'] and player_data['is_alive'] != True: # Check for deaths, Exclue new character
                                    # perks_exclude_fitness_strength = {perk: level for perk, level in player_data['perks'].items() if perk not in ['Fitness', 'Strength']}
                                    self.__deaths.append(copy.deepcopy(player_data))
                                    # player_data['deaths'].append(copy.deepcopy(player_data))
                                    asyncio.run(self.__player_deaths.add_death(player_data['username'], player_data['timestamp'], player_data))
                                    # self.__deaths.append((
                                    #     player_data['username'], 
                                    #     player_data['hours_survived'], 
                                    #     player_data['zombie_kills'], 
                                    #     sum(player_data['perks'].values()), 
                                    #     max(perks_exclude_fitness_strength,key=perks_exclude_fitness_strength.get), 
                                    #     player_data['perks'][max(perks_exclude_fitness_strength,key=perks_exclude_fitness_strength.get)],
                                    #     player_data['coord_x'],
                                    #     player_data['coord_y'],
                                    #     ))

                                self.__player_data[player_data['username']] = player_data
                            else:
                                player_data['totalPlayTime'] = 0
                                player_data['lastLogin'] = time.time()
                                player_data['lastPoll'] = time.time()
                                # player_data['deaths'] = []
                                self.__player_data[player_data['username']] = player_data
                    else:
                        LOGGER.info(f'Player data json file is empty: {filename}')
                else:
                    LOGGER.info(f'Player data file is empty: {filename}')
        save_json_file(json_dict=self.__player_data, file_path='./player_data.json')
    # end update_player_data

    def generate_level_up_msgs(self) -> None:
        level_ups = copy.deepcopy(self.__level_ups)
        self.__level_ups = []
        skill_emojis = read_json_file('./skill_emojis.json')
        for player_name, perk, new_level, old_level in level_ups:
            msg = f"```🎉 {player_name} has leveled up their {perk} to {new_level}! {skill_emojis.get(perk, "")}```"
            self.__level_ups_msgs.append(msg)
    # end generate_level_up_msgs

    def generate_death_msgs(self) -> None:
        deaths = copy.deepcopy(self.__deaths)
        self.__deaths = []
        # for player_name, time_survived_float, zombie_kills, sum_of_perks, highest_skill, skill_level, coord_x, coord_y in deaths:
        for player_data in deaths:
            # In-game time
            in_game_days = int(player_data['time_survived_float'] // 24) # 24 Hours in a Day
            in_game_hours = int(player_data['time_survived_float'] % 24) # The remainder of the days calculations
            in_game_minutes = int((player_data['time_survived_float'] - int(player_data['time_survived_float'])) * 60) # The decimal as a percentage of 60 minutes
            if player_data['time_survived_float'] >= 1:
                in_game_str = f"{in_game_days} days {in_game_hours} hours {in_game_minutes} minutes" if in_game_days > 0 else f"{in_game_hours} hours {in_game_minutes} minutes"
            else:
                in_game_str = "less than 1 hour"
            # Real-life time # 24 Hours In-Game is 1 IRL Hour
            real_days = int(player_data['time_survived_float'] // (24*24)) # 24 Hours is 576 Zomboid Hours
            real_hours = int((player_data['time_survived_float'] % (24*24)) // 24) # 1 Hour is 24 Zomboid Hours
            real_mins = int(((player_data['time_survived_float'] % (24*24)) % 24) // (24/60)) # 1/60 Hours is 0.4 Zomboid Hours
            if real_mins >= 1:
                real_str = f"{real_days} days {real_hours} hours {real_mins} minutes" if real_days > 0 else f"{real_hours} hours {real_mins} minutes"
            else:
                real_str = "less than a minute"
            skill_emojis = read_json_file('./skill_emojis.json')
            perks_exclude_fitness_strength = {perk: level for perk, level in player_data['perks'].items() if perk not in ['Fitness', 'Strength']}
            # emoji = skill_emojis.get(max(perks_exclude_fitness_strength,key=perks_exclude_fitness_strength.get), '')
            highest_skill = max(perks_exclude_fitness_strength, key=lambda perk: perks_exclude_fitness_strength[perk])
            emoji = skill_emojis.get(highest_skill, '')
            url = 'https://b42map.com/?'+str(round(player_data['coords']['x']))+'x'+str(round(player_data['coords']['y']))
            message = [
                f' {player_data['username']} has died.',
                f'Survived in-game: {in_game_str}.',
                f'Real-life: {real_str}.',
                f'Zombie Kills: {player_data['zombie_kills']}.',
                f'Total Skills: {sum(player_data['perks'].values())}.',
                f'Highest Skill: {highest_skill} at {player_data['perks'][highest_skill]}.',
                # f'Locaiton: {url}', # URL needs to be ouside of the code block otherwise it isn't clickable
            ]
            # await pz_rcon_agent.say_to_pz_server(' '.join(message))
            message[0] = '💀 '+message[0]
            message[5] = emoji+' '+message[5]
            self.__deaths_msgs.append(f'```{"\n".join(message)}```Location: {url}') # Location: {url}
    # end generate_death_msgs

    # def repair_player_data(self) -> None:
    #     """Call AFTER merging dupes. Sets default values for missing data keys
    #     """
    #     numeric_players = []
    #     for player in self.__player_data:
    #         if not player.isnumeric():
    #             player_data = self.__player_data[player]
    #             if 'username' not in player_data:
    #                 player_data['username'] = player

    #             if 'display_name' not in player_data:
    #                 player_data['display_name'] = player

    #             if 'character_name' not in player_data:
    #                 player_data['character_name'] = player

    #             if 'user_id' not in player_data:
    #                 player_data['user_id'] = 0

    #             if 'coord_x' not in player_data:
    #                 player_data['coord_x'] = 0
    #             if 'coord_y' not in player_data:
    #                 player_data['coord_y'] = 0
    #             if 'coord_z' not in player_data:
    #                 player_data['coord_z'] = 0

    #             if 'hours_survived' not in player_data and 'hoursSurvived' in player_data:
    #                 player_data['hours_survived'] = player_data['hoursSurvived']
    #                 player_data.pop('hoursSurvived')
    #             elif 'hours_survived' not in player_data:
    #                 player_data['hours_survived'] = 0.0

    #             if 'totalPlayTime' not in player_data:
    #                 player_data['totalPlayTime'] = 0.0

    #             if 'perks' not in player_data and 'skills' in player_data:
    #                 player_data['perks'] = get_default_skills()
    #                 player_data.pop('skills')
    #             elif 'perks' not in player_data:
    #                 player_data['perks'] = get_default_skills()

    #             if 'zombie_kills' not in player_data:
    #                 player_data['zombie_kills'] = 0

    #             if 'survivor_kills' not in player_data:
    #                 player_data['survivor_kills'] = 0

    #             if 'is_alive' not in player_data:
    #                 player_data['is_alive'] = True

    #             old_skills = [
    #                 'Husbandry', 'Farming', 'Blacksmith', 'Woodwork', 
    #                 'Electricity', 'Doctor', 'PlantScavenging', 'FlintKnapping', 
    #                 'Lightfoot', 'LongBlade', 'Blunt', 'Sprinting', 
    #                 'SmallBlade', 'SmallBlunt', 'Sneak', 'MetalWelding', 
    #                 ]
    #             if 'perks' in player_data:
    #                 recreate = False
    #                 for perk in player_data['perks']:
    #                     if perk in old_skills:
    #                         recreate = True
    #                 if recreate:
    #                     player_data.pop('perks')
    #                     player_data['perks'] = get_default_skills()

    #             self.__player_data[player] = player_data
    #         else:
    #             numeric_players.append(player)
    #     for player in numeric_players:
    #         LOGGER.info(f'Removed {self.__player_data.pop(player)} from player_data.jon')
    #     save_json_file(json_dict=self.__player_data, file_path='./player_data.json')
    # # end repair_player_data

    # def merge_dupes(self) -> None:
    #     # all_player_data = read_json_file(file_path='./player_data.json')
    #     drop_players = []
    #     for player in self.__player_data:
    #         if player != player.lower() and player.lower() in self.__player_data:
    #             player_data_a = self.__player_data[player.lower()] # Lower-cased player entry
    #             player_data_b = self.__player_data[player] # Non lower-cased player entry
    #             # if player.lower() == 'pedguin': print(player_data_a, '\n\n', player_data_b, '\n\n')
    #             for key in player_data_b.keys():
    #                 # if player.lower() == 'pedguin': print(player, isinstance(player_data_a[key], int), isinstance(player_data_a[key], float))
    #                 if isinstance(player_data_a[key], int) or isinstance(player_data_a[key], float):
    #                     if player_data_a[key] < player_data_b[key]:
    #                         player_data_a[key] = player_data_b[key]
    #                 else:
    #                     player_data_a[key] = player_data_b[key]
    #             # if player.lower() == 'pedguin': print(self.__player_data[player], '\n\n', player_data_a, '\n\n', player_data_b, '\n\n')

    #             self.__player_data[player.lower()] = player_data_a
    #             # if player.lower() == 'pedguin': print(self.__player_data[player.lower()])
    #             drop_players.append(player)
    #     if len(drop_players) > 0:
    #         for player in drop_players:
    #             self.__player_data.pop(player)
    #     save_json_file(json_dict=self.__player_data, file_path='./player_data.json')
    # # end merge_dupes

    def update_player_total_play_time(self, username:str) -> bool:
        if username in self.__player_data:
            if (time.time() - self.__player_data[username]['lastPoll']) < (2*self.__settings['MAX_POLLING_RATE']): # Only increment total play time if time since last poll is less than twice the max polling rate 
                self.__player_data[username]['totalPlayTime'] += (time.time() - self.__player_data[username]['lastPoll'])
                self.__player_data[username]['lastPoll'] = time.time()
                save_json_file(json_dict=self.__player_data, file_path='./player_data.json')
                return True
            else: # Do not increment total play time, instead set new lastPoll
                self.__player_data[username]['lastPoll'] = time.time()
                save_json_file(json_dict=self.__player_data, file_path='./player_data.json')
                return False
        else:
            return False
    # end add_player_time_played

    def update_player_last_login(self, username:str, lastLogin:float) -> bool:
        if username in self.__player_data:
            self.__player_data[username]['lastLogin'] = lastLogin
            save_json_file(json_dict=self.__player_data, file_path='./player_data.json')
            return True
        else:
            return False
    # end add_player_login_time

    # def update_player_last_poll(self, username:str, lastPoll:float) -> bool:
    #     if username in self.__player_data:
    #         self.__player_data[username]['lastPoll'] = lastPoll
    #         save_json_file(json_dict=self.__player_data, file_path='./player_data.json')
    #         return True
    #     else:
    #         return False
    # # end add_player_login_time

    def get_player_data(self, username:str = "") -> dict:
        """Returns a dictionary of either all player data or just one player's data

        Returns:
            dict: player data
        """
        if username != "":
            if username in self.__player_data:
                return copy.deepcopy(self.__player_data[username])
            else:
                return copy.deepcopy(self.__player_data)
        else:
            return copy.deepcopy(self.__player_data)
    # end get_player_data

    def get_world_data(self, param:str = "") -> dict:
        if param != "":
            if param in self.__world_data:
                return copy.deepcopy(self.__world_data[param])
            else:
                return copy.deepcopy(self.__world_data)
        else:
            return copy.deepcopy(self.__world_data)
    # end get_world_data

    def get_level_ups_msgs(self) -> list[str]:
        curr_val = copy.deepcopy(self.__level_ups_msgs)
        self.__level_ups_msgs = []
        return curr_val
    # end get_level_ups

    def get_deaths_msgs(self) -> list[str]:
        curr_val = copy.deepcopy(self.__deaths_msgs)
        self.__deaths_msgs = []
        return curr_val
    # end get_deaths

    async def get_list_of_player_death_names(self) -> list[str]:
        return await self.__player_deaths.get_list_usernames()
    # end get_list_of_players

    async def get_death(self, death_id:int) -> dict:
        return await self.__player_deaths.get_death(death_id)
    # end get_death

    async def get_list_of_deaths(self, username:str = '', quantity:int = 10) -> list[tuple[int, float, str]]:
        return await self.__player_deaths.get_list_of_deaths(username, quantity)
    # end get_list_of_deaths

    async def get_list_around_death_id(self, death_id:int, radius:int=5) -> list[tuple[int, float, str]]:
        return await self.__player_deaths.get_list_around(death_id, radius)
    # end get_list_around_death_id

    def toggle_running(self) -> None:
        if self.__running:
            self.__running = False
        else:
            self.__running = True
    # end toggle_running

    def run_agent(self) -> None:
        last_poll = time.time()
        while self.__running:
            if (time.time() - last_poll) > (self.__settings['POLLING_RATE'] + self.__dynamic_delay):
                self.poll_player_data()
                self.generate_level_up_msgs()
                self.generate_death_msgs()
                asyncio.run(self.__player_deaths.read_usernames())
                last_poll = time.time()
        # end while
    # end run_agent
# end PerkCollector

if __name__ == '__main__': # For testing purposes
    newAgent = Agent_Player_Data()
    newAgent.run_agent()
    # newAgent.poll_player_data()
    # newAgent.update_player_data()
    # print(newAgent.get_player_data())