# Developed by Anthony Castillo (ComradeWolf) for Peter Mann (Pedguin)
# Last Update: 04/05/2026 (DD/MM/YYYY)

import discord
# from discord.ext import commands, tasks
from discord import app_commands
from discord.ext import commands
import time
import logging
LOGGER: logging.Logger = logging.getLogger("bot")
import difflib
from datetime import datetime
# from class_bot import Discord_Bot
# import class_bot

from shared_functions.player_data_functions import read_json_file, get_default_skills
from agents.pz_rcon import Agent_PZ_RCON
from agents.player_data import Agent_Player_Data
from classes.bot import Discord_Bot

class Project_Zomboid_Commands(commands.Cog):
    def __init__(self, bot:Discord_Bot, pz_rcon_agent:Agent_PZ_RCON, player_data_agent:Agent_Player_Data):
        self.__bot = bot
        self.__pz_rcon_agent = pz_rcon_agent
        self.__player_data_agent = player_data_agent
    # end __init__

    @app_commands.command(name="online", description="Show currently online players.")
    async def online_slash(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        if not self.__pz_rcon_agent.get_online_players():
            await interaction.followup.send("```🟢 - No players are currently online.```")
            return
        lines = []
        for player in sorted(self.__pz_rcon_agent.get_online_players()):
            if player in self.__player_data_agent.get_player_data():
                duration = time.time() - self.__player_data_agent.get_player_data(player)['lastLogin'] #player_sessions.get(player, now)
                h, m, s = int(duration//3600), int((duration%3600)//60), int((duration%(60*60)%60))
                lines.append(f"- {player} ({h}h {m}m {s}s)")
        await interaction.followup.send(f"```🟢 - Players Online (Session Time):\n" + "\n".join(lines) + f"\n\nTotal: {len(self.__pz_rcon_agent.get_online_players())}```")
    # end online_slash

    @app_commands.command(name="playtime", description="Show total playtime for a player.")
    @app_commands.describe(target="Player name or 'all'")
    async def playtime_slash(self, interaction: discord.Interaction, target: str = "all"):
        await interaction.response.defer(thinking=True)
        if target == "all":
            player_times = []
            all_player_data = self.__player_data_agent.get_player_data()
            for player in all_player_data:
                if all_player_data[player]['access_level'] != "admin": # Exclude admins from playtime leaderboard
                    if player in self.__pz_rcon_agent.get_online_players():
                        player_times.append((player, all_player_data[player]['totalPlayTime']+(time.time()-all_player_data[player]['lastPoll'])))
                    else:
                        player_times.append((player, all_player_data[player]['totalPlayTime']))
            player_times = sorted(player_times, key=lambda tup: tup[1], reverse=True)
            lines = []
            for p, sec in player_times[:10]: # Top 10 (arrays/lists start at 0 and this syntax goes up to, but does not include the last index)
                h, m, s = int(sec//3600), int((sec%3600)//60), int((sec%3600)%60)
                status = "🟢" if p in self.__pz_rcon_agent.get_online_players() else "🔴"
                lines.append(f"{status} - {p}: {h}h {m}m {s}s")
            await interaction.followup.send("```🕒 - Top 10 Players by Total Playtime:\n" + "\n".join((lines)) + "```")
        # elif target.lower() in self.__player_data_agent.get_player_data(): # A Singlar Player
        #     player_data = self.__player_data_agent.get_player_data()[target.lower()]
        #     h, m, s = 0, 0, 0
        #     if target.lower() in self.__pz_rcon_agent.get_online_players():
        #         player_time = player_data['totalPlayTime']+(time.time()-player_data['lastPoll'])
        #         h, m, s = int(player_time//3600), int((player_time%3600)//60), int((player_time%3600)%60)
        #     else:
        #         h, m, s = int(player_data['totalPlayTime']//3600), int((player_data['totalPlayTime']%3600)//60), int((player_data['totalPlayTime']%3600)%60)
        #     status = "🟢" if target.lower() in self.__pz_rcon_agent.get_online_players() else "🔴"
        #     await interaction.followup.send(f"```{status} - {target.capitalize()} has played for {h}h {m}m {s}s in total.```")
        elif len(difflib.get_close_matches(target, self.__player_data_agent.get_player_data().keys())) > 0: # Get closest match
            matches = difflib.get_close_matches(target, self.__player_data_agent.get_player_data().keys())
            player_data = self.__player_data_agent.get_player_data(matches[0])
            h, m, s = 0, 0, 0
            if target in self.__pz_rcon_agent.get_online_players():
                player_time = player_data['totalPlayTime']+(time.time()-player_data['lastPoll'])
                h, m, s = int(player_time//3600), int((player_time%3600)//60), int((player_time%3600)%60)
            else:
                h, m, s = int(player_data['totalPlayTime']//3600), int((player_data['totalPlayTime']%3600)//60), int((player_data['totalPlayTime']%3600)%60)
            status = "🟢" if matches[0] in self.__pz_rcon_agent.get_online_players() else "🔴"
            await interaction.followup.send(f"```{status} - {matches[0]} has played for {h}h {m}m {s}s in total.```")
        else:
            await interaction.followup.send(f'```Could not find a player named {target}.```')
    # end playtime_slash

    @app_commands.command(name="survived", description="Shows the total time a player's current character has survived for in in-game hours.")
    @app_commands.describe(target="Player name or 'all'")
    async def survived_slash(self, interaction: discord.Interaction, target: str = "all"):
        await interaction.response.defer(thinking=True)
        if target == "all":
            player_times = []
            all_player_data = self.__player_data_agent.get_player_data()
            for player in all_player_data:
                if all_player_data[player]['access_level'] != "admin": # Exclude admins from survival time leaderboard
                    player_times.append((all_player_data[player]['username'], all_player_data[player]['time_survived_float']%24, all_player_data[player]['time_survived_float']//24, all_player_data[player]['time_survived_float']))
            player_times = sorted(player_times, key=lambda tup: tup[3], reverse=True)
            lines = []
            for p, hours, days, _ in player_times[:10]: # Top 10 (arrays/lists start at 0 and this syntax goes up to, but does not include the last index)
                status = "🟢" if p in self.__pz_rcon_agent.get_online_players() else "🔴"
                lines.append(f"{status} - {p}: {int(days)} days {int(hours)} hours")
            await interaction.followup.send("```🕒 - Top 10 Current Character by In-Game Survival Hours:\n" + "\n".join((lines)) + "```")
        # elif target.lower() in self.__player_data_agent.get_player_data(): # A Singlar Player
        #     player_data = self.__player_data_agent.get_player_data()[target.lower()]
        #     days = int(player_data['time_survived_float']//24)
        #     hours = int(player_data['time_survived_float']%24)
        #     status = "🟢" if target.lower() in self.__pz_rcon_agent.get_online_players() else "🔴"
        #     await interaction.followup.send(f"```{status} - {target.capitalize()} has survived for {days} days and {hours} hours in-game.```")
        elif len(difflib.get_close_matches(target, self.__player_data_agent.get_player_data().keys())) > 0: # Get closest match
            matches = difflib.get_close_matches(target, self.__player_data_agent.get_player_data().keys())
            player_data = self.__player_data_agent.get_player_data(matches[0])
            days = int(player_data['time_survived_float']//24)
            hours = int(player_data['time_survived_float']%24)
            status = "🟢" if matches[0] in self.__pz_rcon_agent.get_online_players() else "🔴"
            await interaction.followup.send(f"```{status} - {matches[0]} has survived for {days} days and {hours} hours in-game.```")
        else:
            await interaction.followup.send(f'```Could not find a player named {target}.```')
    # end survived_slash

    @app_commands.command(name="zombies", description="Shows a player's total zombie kills.")
    @app_commands.describe(target="Player name or 'all'")
    async def zombies_slash(self, interaction: discord.Interaction, target: str = "all"):
        await interaction.response.defer(thinking=True)
        if target == "all":
            total_zombie_kills = 0
            player_zombie_kills = []
            all_player_data = self.__player_data_agent.get_player_data()
            for player_data in all_player_data:
                if all_player_data[player_data]['access_level'] != "admin": # Exclude admins from zombie kill leaderboard
                    player_zombie_kills.append((all_player_data[player_data]['username'], all_player_data[player_data]['zombie_kills']))
                    total_zombie_kills += all_player_data[player_data]['zombie_kills']
            player_zombie_kills = sorted(player_zombie_kills, key=lambda tup: tup[1], reverse=True)
            lines = []
            for p, kills in player_zombie_kills[:10]: # Top 10 (arrays/lists start at 0 and this syntax goes up to, but does not include the last index)
                status = "🟢" if p in self.__pz_rcon_agent.get_online_players() else "🔴"
                lines.append(f"{status} - {p}: {kills} zombies")
            await interaction.followup.send(f"```🕒 - Top 10 Current Character by Zombie Kills (Total: {total_zombie_kills}):\n" + "\n".join((lines)) + "```")
        # elif target.lower() in self.__player_data_agent.get_player_data(): # A Singlar Player
        #     player_data = self.__player_data_agent.get_player_data()[target.lower()]
        #     status = "🟢" if target.lower() in self.__pz_rcon_agent.get_online_players() else "🔴"
        #     await interaction.followup.send(f"```{status} - {target.capitalize()} has killed {player_data['zombie_kills']} zombies.```")
        elif len(difflib.get_close_matches(target, self.__player_data_agent.get_player_data().keys())) > 0: # Get closest match
            matches = difflib.get_close_matches(target, self.__player_data_agent.get_player_data().keys())
            player_data = self.__player_data_agent.get_player_data(matches[0])
            status = "🟢" if matches[0] in self.__pz_rcon_agent.get_online_players() else "🔴"
            await interaction.followup.send(f"```{status} - {matches[0]} has killed {player_data['zombie_kills']} zombies.```")
        else:
            await interaction.followup.send(f'```Could not find a player named {target}.```')
    # end zombies_slash

    # # Command suspended for non-pvp server  
    # @app_commands.command(name="survivors", description="Shows a player's total survivor kills.")
    # @app_commands.describe(target="Player name or 'all'")
    # async def survivors_slash(self, interaction: discord.Interaction, target: str):
    #     await interaction.response.defer(thinking=True)
    #     if target.lower() == "all":
    #         player_times = []
    #         for player in self.__player_data_agent.get_player_data():
    #             player_data = self.__player_data_agent.get_player_data()[player]
    #             player_times.append((player_data['username'], player_data['survivor_kills']))
    #         player_times = sorted(player_times, key=lambda tup: tup[1], reverse=True)
    #         lines = []
    #         for p, kills in player_times[:10]: # Top 10 (arrays/lists start at 0 and this syntax goes up to, but does not include the last index)
    #             status = "🟢" if p in self.__pz_rcon_agent.get_online_players() else "🔴"
    #             lines.append(f"{status} - {p.capitalize()}: {kills} survivors")
    #         await interaction.folloutup.send("```🕒 - Top 10 Current Character by Survivors Kills:\n" + "\n".join((lines)) + "```")
    #     elif target.lower() in self.__player_data_agent.get_player_data(): # A Singlar Player
    #         player_data = self.__player_data_agent.get_player_data()[target.lower()]
    #         survivors = player_data['survivor_kills']
    #         status = "🟢" if target.lower() in self.__pz_rcon_agent.get_online_players() else "🔴"
    #         await interaction.followup.send(f"```{status} - {target.capitalize()} has killed {survivors} survivors.```")
    #     else:
    #         await interaction.followup.send(f'```Could not find a player named {target}.```')
    # # end survivors_slash

    @app_commands.command(name="skills", description="Show a player's skills or leaderboard for a skill")
    @app_commands.describe(target="Nothing, a skill name or a player name.")
    async def skills_slash(self, interaction: discord.Interaction, target:str = ""): #target2:str=None
        await interaction.response.defer(thinking=True)
        skill_aliases = read_json_file('./skill_aliases.json')
        skill_emojis = read_json_file('./skill_emojis.json')
        lines = []
        if target == '': # Show leaderboard
            combined = []
            all_player_data = self.__player_data_agent.get_player_data()
            for player_data in all_player_data:
                if all_player_data[player_data]['access_level'] != "admin": # Exclude admins from total skill leaderboard
                    combined.append((all_player_data[player_data]['username'], sum(all_player_data[player_data]['perks'].values()),))
            top = sorted(combined, key=lambda x: x[1], reverse=True)[:10]
            for tuple in top:
                status = "🟢" if tuple[0] in [pl for pl in self.__pz_rcon_agent.get_online_players()] else "🔴"
                lines.append(f'{status} - {tuple[0]}: {tuple[1]}')
            await interaction.followup.send(f"```📊 - Top 10 Players by Total Skills:\n" + "\n".join(lines) + "```")
        # elif target_lower in self.__player_data_agent.get_player_data(): # Player specific
        #     player_data = self.__player_data_agent.get_player_data()[target_lower]
        #     skills = []
        #     for perk in sorted(player_data['perks']):
        #         if player_data['perks'][perk] > 0:
        #             skills.append((perk, player_data['perks'][perk]))
        #     skills = sorted(skills, key=lambda x: x[1], reverse=True)
        #     for tuple in skills:
        #         emoji = skill_emojis.get(tuple[0], '')
        #         lines.append(f'{emoji} {tuple[0]}: {tuple[1]}')
        #     status = "🟢" if target_lower in [pl.lower() for pl in self.__pz_rcon_agent.get_online_players()] else "🔴"
        #     await interaction.followup.send(f"```{status} - {player_data['username']}'s Skills (Total: {sum(tuple[1] for tuple in skills)})\n" + "\n".join(lines) + "```")
        elif target in skill_aliases: # Skill alias specific
            skill_alias = skill_aliases[target]
            emoji = skill_emojis.get(skill_alias, '')
            combined = []
            all_player_data = self.__player_data_agent.get_player_data()
            for player_data in all_player_data:
                combined.append((all_player_data[player_data]['username'], all_player_data[player_data]['perks'][skill_alias],))
            combined = sorted(combined, key=lambda x: x[1], reverse=True)[:10]
            for tuple in combined:
                status = "🟢" if tuple[0] in [player for player in self.__pz_rcon_agent.get_online_players()] else "🔴"
                lines.append(f'{status} - {tuple[0]}: {tuple[1]}')
            await interaction.followup.send(f"```{emoji} - Top 10 Players by {skill_alias}:\n" + "\n".join(lines) + "```")
        # elif target.capitalize() in get_default_skills(): # Skill specific
        #     target_capitalize = target.capitalize()
        #     emoji = skill_emojis.get(target_capitalize, '')
        #     combined = []
        #     all_player_data = self.__player_data_agent.get_player_data()
        #     for player_data in all_player_data:
        #         combined.append((player_data, all_player_data[player_data]['perks'][target_capitalize],))
        #     combined = sorted(combined, key=lambda x: x[1], reverse=True)[:10]
        #     for tuple in combined:
        #         status = "🟢" if tuple[0].lower() in [player.lower() for player in self.__pz_rcon_agent.get_online_players()] else "🔴"
        #         lines.append(f'{status} - {tuple[0]}: {tuple[1]}')
        #     await interaction.followup.send(f"```{emoji} - Top 10 Players by {target_capitalize}:\n" + "\n".join(lines) + "```")
        elif len(difflib.get_close_matches(target, self.__player_data_agent.get_player_data().keys())) > 0: # Get closest match of players
            matches = difflib.get_close_matches(target, self.__player_data_agent.get_player_data().keys())
            player_data = self.__player_data_agent.get_player_data(matches[0])
            skills = []
            for perk in sorted(player_data['perks']):
                if player_data['perks'][perk] > 0:
                    skills.append((perk, player_data['perks'][perk]))
            skills = sorted(skills, key=lambda x: x[1], reverse=True)
            for tuple in skills:
                emoji = skill_emojis.get(tuple[0], '')
                lines.append(f'{emoji} {tuple[0]}: {tuple[1]}')
            status = "🟢" if matches[0] in [pl for pl in self.__pz_rcon_agent.get_online_players()] else "🔴"
            await interaction.followup.send(f"```{status} - {player_data['username']}'s Skills (Total: {sum(tuple[1] for tuple in skills)})\n" + "\n".join(lines) + "```")
        elif len(difflib.get_close_matches(target, get_default_skills().keys())) > 0: # Get closest match of skills
            matches = difflib.get_close_matches(target, get_default_skills().keys())
            emoji = skill_emojis.get(matches[0], '')
            combined = []
            all_player_data = self.__player_data_agent.get_player_data()
            for player_data in all_player_data:
                if all_player_data[player_data]['access_level'] != "admin": # Exclude admins from individual skill leaderboards
                    combined.append((player_data, all_player_data[player_data]['perks'][matches[0]],))
            combined = sorted(combined, key=lambda x: x[1], reverse=True)[:10]
            for tuple in combined:
                status = "🟢" if tuple[0] in [player for player in self.__pz_rcon_agent.get_online_players()] else "🔴"
                lines.append(f'{status} - {tuple[0]}: {tuple[1]}')
            await interaction.followup.send(f"```{emoji} - Top 10 Players by {matches[0]}:\n" + "\n".join(lines) + "```")
        else:
            await interaction.followup.send(f"```Could not find player or skill with name {target}```")
    # end skill_slash

    @app_commands.command(name="professions", description="Show a player's profession, a list of players for a profession, or the top professions.")
    @app_commands.describe(target="Profession name, player name or 'top'.")
    async def professions_slash(self, interaction: discord.Interaction, target:str = "top"): #target2:str=None
        await interaction.response.defer(thinking=True)
        if target == "top":
            profession_list = {}
            all_player_data = self.__player_data_agent.get_player_data()
            for player_data in all_player_data:
                if all_player_data[player_data]['access_level'] != "admin":
                    if all_player_data[player_data]['profession'] not in profession_list:
                        profession_list[all_player_data[player_data]['profession']] = 1
                    else:
                        profession_list[all_player_data[player_data]['profession']] += 1
            profession_top_list = []
            for key, value in profession_list.items():
                profession_top_list.append((key, value))
            profession_top_list = sorted(profession_top_list, key=lambda x: x[1], reverse=True)[:10]
            await interaction.followup.send(f"```📊 - Top 10 Most Popular Professions:\n" + "\n".join([f"{profession}: {count}" for profession, count in profession_top_list]) + "```")
        elif len(difflib.get_close_matches(target, self.__player_data_agent.get_player_data().keys())) > 0: # Get closest match of players
            matches = difflib.get_close_matches(target, self.__player_data_agent.get_player_data().keys())
            player_data = self.__player_data_agent.get_player_data(matches[0])
            status = "🟢" if matches[0] in [pl for pl in self.__pz_rcon_agent.get_online_players()] else "🔴"
            await interaction.followup.send(f"```{status} - {player_data['username']}'s Profession: {player_data['profession']}```")
        else:
            profession_list = {}
            all_player_data = self.__player_data_agent.get_player_data()
            for player_data in all_player_data:
                if all_player_data[player_data]['access_level'] != "admin":
                    if all_player_data[player_data]['profession'] not in profession_list:
                        profession_list[all_player_data[player_data]['profession']] = [player_data]
                    else:
                        profession_list[all_player_data[player_data]['profession']].append(player_data)
            if len(difflib.get_close_matches(target, profession_list)) > 0: # Get closest match of professions
                matches = difflib.get_close_matches(target, profession_list.keys())
                lines = []
                for player in profession_list[matches[0]]:
                    status = "🟢" if player in [pl for pl in self.__pz_rcon_agent.get_online_players()] else "🔴"
                    lines.append(f'{status} - {all_player_data[player]["username"]}')
                await interaction.followup.send(f"```Players with the {matches[0]} profession:\n" + "\n".join(lines) + "```")
            else:
                await interaction.followup.send(f"```Could not find player or profession with name {target}```")
    # end professions_slash

    @app_commands.command(name="traits", description="Show a player's traits or a list of players for a trait")
    @app_commands.describe(target="Trait name, player name or 'top'.")
    async def traits_slash(self, interaction: discord.Interaction, target:str = "top"): #target2:str=None
        await interaction.response.defer(thinking=True)
        if target == "top": # Default, leaderboard
            traits_list = {}
            all_player_data = self.__player_data_agent.get_player_data()
            for player_data in all_player_data:
                if all_player_data[player_data]['access_level'] != "admin":
                    for trait in all_player_data[player_data]['traits']:
                        if trait not in traits_list:
                            traits_list[trait] = 1
                        else:
                            traits_list[trait] += 1
            traits_top_list = [] 
            for key, value in traits_list.items():
                traits_top_list.append((key, value))
            traits_top_list = sorted(traits_top_list, key=lambda x: x[1], reverse=True)[:10]
            await interaction.followup.send(f"```📊 - Top 10 Most Popular Traits:\n" + "\n".join([f"{trait}: {count}" for trait, count in traits_top_list]) + "```")
        elif len(difflib.get_close_matches(target, self.__player_data_agent.get_player_data().keys())) > 0: # Get closest match of players
            trait_lines = []
            matches = difflib.get_close_matches(target, self.__player_data_agent.get_player_data().keys())
            player_data = self.__player_data_agent.get_player_data(matches[0])
            for trait in player_data['traits']:
                trait_lines.append(f'- {trait}')
            status = "🟢" if matches[0] in [pl for pl in self.__pz_rcon_agent.get_online_players()] else "🔴"
            await interaction.followup.send(f"```{status} - {player_data['username']}'s Traits:\n" + "\n".join(trait_lines) + "```")
        else:
            trait_list = {}
            all_player_data = self.__player_data_agent.get_player_data()
            for player_data in all_player_data:
                if all_player_data[player_data]['access_level'] != "admin":
                    for trait in all_player_data[player_data]['traits']:
                        if trait not in trait_list:
                            trait_list[trait] = [player_data]
                        else:
                            trait_list[trait].append(player_data)
            if len(difflib.get_close_matches(target, trait_list)) > 0: # Get closest match of traits
                matches = difflib.get_close_matches(target, trait_list.keys())
                lines = []
                for player in trait_list[matches[0]]:
                    status = "🟢" if player in [pl for pl in self.__pz_rcon_agent.get_online_players()] else "🔴"
                    lines.append(f'{status} - {all_player_data[player]["username"]}')
                await interaction.followup.send(f"```Players with the {matches[0]} trait:\n" + "\n".join(lines) + "```")
            else:
                await interaction.followup.send(f"```Could not find player or trait with name {target}```")
    # end traits_slash

    @app_commands.command(name="stats", description="Show all of a player's stats")
    @app_commands.describe(target="A player's name.")
    async def stats_slash(self, interaction: discord.Interaction, target:str): #target2:str=None
        await interaction.response.defer(thinking=True)
        if len(difflib.get_close_matches(target, self.__player_data_agent.get_player_data().keys())) > 0:
            matches = difflib.get_close_matches(target, self.__player_data_agent.get_player_data().keys())
            player_data = self.__player_data_agent.get_player_data(matches[0])
            lines = []
            status = "🟢" if matches[0] in [pl for pl in self.__pz_rcon_agent.get_online_players()] else "🔴"
            lines.append(f"{status} - {player_data['username']}\'s Stats\n")
            lines.append(f"Username: {player_data['username']}")
            h, m, s = 0, 0, 0
            if target in self.__pz_rcon_agent.get_online_players():
                player_time = player_data['totalPlayTime']+(time.time()-player_data['lastPoll'])
                h, m, s = int(player_time//3600), int((player_time%3600)//60), int((player_time%3600)%60)
            else:
                h, m, s = int(player_data['totalPlayTime']//3600), int((player_data['totalPlayTime']%3600)//60), int((player_data['totalPlayTime']%3600)%60)
            lines.append(f"Total Playtime: {h}h {m}m {s}s")
            lines.append(f"Last Login: {datetime.fromtimestamp(round(player_data['lastLogin'])).strftime("%B %d, %Y, %H:%M:%S")}")
            lines.append(f"Character Name: {player_data['character_name']}")
            lines.append(f"Faction: {player_data['faction']}")
            lines.append(f"Profession: {player_data['profession']}")
            lines.append(f"Traits: {', '.join(player_data['traits'])}")
            skill_emojis = read_json_file('./skill_emojis.json')
            skills = []
            for perk in player_data['perks']:
                if player_data['perks'][perk] > 0:
                    skills.append((perk, player_data['perks'][perk]))
            skills = sorted(skills, key=lambda x: x[1], reverse=True)
            lines.append(f"Skills (Total: {sum(tuple[1] for tuple in skills)}):")
            for tuple in skills:
                emoji = skill_emojis.get(tuple[0], '')
                lines.append(f'\t{emoji} {tuple[0]}: {tuple[1]}')
            lines.append(f"Deaths: {len(player_data['deaths'])}")
            if len(player_data['deaths']) > 0:
                lines.append(f"Last Death: {datetime.fromtimestamp(round(player_data['deaths'][-1]['timestamp'])).strftime("%B %d, %Y, %H:%M:%S")}")
            days = int(player_data['time_survived_float']//24)
            hours = int(player_data['time_survived_float']%24)
            lines.append(f"Has Survived For: {days} days and {hours} hours in-game.")
            lines.append(f"Zombie Kills: {player_data['zombie_kills']}")
            # lines.append(f"Survivor Kills: {player_data['survivor_kills']}") # Ommitted for PvE server
            lines.append(f"\nLast Updated: {datetime.fromtimestamp(round(player_data['timestamp'])).strftime("%B %d, %Y, %H:%M:%S")}")
            await interaction.followup.send(f"```{'\n'.join(lines)}```")
        elif target == '':
            await interaction.followup.send(f"```Please enter a username```")
        else:
            await interaction.followup.send(f"```Could not find player a named {target}```")
    # end stats_slash

    @app_commands.command(name="deaths", description="Show a list of the most recent deaths (for an optional target).")
    @app_commands.describe(target="A player's name, a death id, or 'all'.", quantity="The number of deaths to show (or a radius when scouting).", scout="Look around death id (Default: False).")
    async def deaths_slash(self, interaction: discord.Interaction, target:str, quantity:int=10, scout:bool=False): #target2:str=None
        await interaction.response.defer(thinking=True)
        if target.isnumeric():
            if not scout:
                player_death = await self.__player_data_agent.get_death(int(target))
                lines = []
                url = 'https://b42map.com/?'+str(round(player_death['coords']['x']))+'x'+str(round(player_death['coords']['y']))+'x'+str(round(player_death['coords']['z']))
                lines.append(f'Username: {player_death['username']}')
                lines.append(f'Time of Death: {datetime.fromtimestamp(round(player_death['timestamp'])).strftime("%B %d, %Y, %H:%M:%S")}')
                lines.append(f'Character Name: {player_death['character_name']}')
                lines.append(f'Profession: {player_death['profession']}')
                lines.append(f'Time Survived: {player_death['time_survived_string']}')
                lines.append(f'Zombie Kills: {player_death['zombie_kills']}')
                lines.append(f'Top 3 Perks:')
                perks = []
                skill_emojis = read_json_file('./skill_emojis.json')
                for perk in player_death['perks']:
                    perks.append((perk, player_death['perks'][perk], skill_emojis.get(perk)))
                perks = sorted(perks, key=lambda x: x[1], reverse=True)
                lines.append(f'\t{perks[0][2]} {perks[0][0]}: {perks[0][1]}')
                lines.append(f'\t{perks[1][2]} {perks[1][0]}: {perks[1][1]}')
                lines.append(f'\t{perks[2][2]} {perks[2][0]}: {perks[2][1]}')
                await interaction.followup.send(f"```💀 - Death Report #{target} for {player_death['username']}:\n" + "\n".join(lines) + "```"+f'{url}')
            else:
                player_deaths = await self.__player_data_agent.get_list_around_death_id(int(target), quantity)
                lines = [
                    f"📊 - {quantity*2} Deaths Surrounding Report #{target}:",
                    '\nID - Datetime\tUsername'
                ]
                for death in player_deaths:
                    lines.append(f'\n{death[0]} - {datetime.fromtimestamp(round(death[1])).strftime("%B %d, %Y, %H:%M:%S")}\t{death[2]}')
                await interaction.followup.send(self.format_output(lines))
        elif target == 'all': # Default
            all_deaths = await self.__player_data_agent.get_list_of_deaths(quantity=quantity)
            recent_deaths = sorted(all_deaths, key=lambda x: x[1], reverse=True)
            lines = [
                f"📊 - Recent {quantity} Deaths:",
                '\nID - Datetime\tUsername'
                ]
            for death in recent_deaths:
                lines.append(f'\n{death[0]} - {datetime.fromtimestamp(round(death[1])).strftime("%B %d, %Y, %H:%M:%S")}\t{death[2]}')
            # all_player_data = self.__player_data_agent.get_player_data()
            # combined = []
            # for player in all_player_data:
            #     combined.append((player, len(all_player_data[player]['deaths'])))
            # top = sorted(combined, key=lambda x: x[1], reverse=True)[:10]
            # lines = []
            # for tuple in top:
            #     status = "🟢" if tuple[0] in [pl for pl in self.__pz_rcon_agent.get_online_players()] else "🔴"
            #     lines.append(f'{status} - {tuple[0]}: {tuple[1]}')
            await interaction.followup.send(self.format_output(lines))
        elif len(difflib.get_close_matches(target, await self.__player_data_agent.get_list_of_player_death_names())) > 0:
            matches = difflib.get_close_matches(target, await self.__player_data_agent.get_list_of_player_death_names())
            player_deaths = await self.__player_data_agent.get_list_of_deaths(matches[0], quantity)
            recent_deaths = sorted(player_deaths, key=lambda x: x[1], reverse=True)
            status = "🟢" if matches[0] in [pl for pl in self.__pz_rcon_agent.get_online_players()] else "🔴"
            lines = [
                f"{status} - {matches[0]}\'s Deaths (Total: {len(player_deaths)}):",
                '\nID - Datetime\tUsername'
                ]
            for death in recent_deaths:
                lines.append(f'\n{death[0]} - {datetime.fromtimestamp(round(death[1])).strftime("%B %d, %Y, %H:%M:%S")}\t{death[2]}')
            # player_data = self.__player_data_agent.get_player_data(matches[0])
            # lines = []
            # if len(player_data['deaths']) > 0:
            #     for index, death in enumerate(player_data['deaths']):
            #         url = 'https://b42map.com/?'+str(round(death['coords']['x']))+'x'+str(round(death['coords']['y']))
            #         lines.append(f"{index+1} - {datetime.fromtimestamp(round(death['timestamp'])).strftime("%B %d, %Y, %H:%M:%S")} {url}")
            # else:
            #     lines.append(f"This player has not had any deaths")
            await interaction.followup.send(self.format_output(lines))
        else:
            await interaction.followup.send(f"```Could not find player a named {target}```")
    # end deaths_slash

    @app_commands.command(name="time", description="Show world time.")
    async def time_slash(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        await interaction.followup.send(f"```🕒 - Current World Time: {self.get_time(self.__player_data_agent.get_world_data('time'))}```")
    # end time_slash
    
    @app_commands.command(name="weather", description="Show world information")
    @app_commands.describe(target="time, season, temperature, weather or wind.")
    async def world_slash(self, interaction: discord.Interaction, target:str = ""): #target2:str=None
        await interaction.response.defer(thinking=True)
        if target == "": # Default
            world_data = self.__player_data_agent.get_world_data()
            if world_data:
                lines = []
                lines.append(f"🌎 - Weather Report - 🌎\n")
                lines.append(f"🕒 Time: {self.get_time(world_data['time'])}")
                lines.append(f"🍂 Season: {world_data['season']['name']}")
                lines.append(f"🌡️ Temperature: {round(world_data['temperature']['base'], 1)}°C")
                lines.append(f"⛅ Weather:\n{self.get_weather_description(world_data['weather'])}")
                wind_direction = self.get_wind_direction(world_data['wind']['angle_degrees'])
                lines.append(f"💨 Wind:\n{self.get_wind_description(world_data['wind'])}")
                await interaction.followup.send(f"```{'\n'.join(lines)}```")
            else:
                await interaction.followup.send(f"```No world data available.```")
        elif target == "time":
            world_data = self.__player_data_agent.get_world_data('time')
            if world_data:
                await interaction.followup.send(f"```🕒 - Current World Time: {self.get_time(self.__player_data_agent.get_world_data('time'))}```")
            else:
                await interaction.followup.send(f"```No world data available.```")
        elif target == "season":
            world_data = self.__player_data_agent.get_world_data('season')
            if world_data:
                await interaction.followup.send(f"```🍂 - Current Season: {world_data['name']}```")
            else:
                await interaction.followup.send(f"```No world data available.```")
        elif target == "temperature" or target == "temp":
            world_data = self.__player_data_agent.get_world_data('temperature')
            if world_data:
                await interaction.followup.send(f"```🌡️ - Current Temperature: {round(world_data['base'], 1)}°C```")
            else:
                await interaction.followup.send(f"```No world data available.```")
        elif target == "weather":
            world_data = self.__player_data_agent.get_world_data('weather')
            if world_data:
                await interaction.followup.send(f"```⛅ - Current Weather:\n{self.get_weather_description(world_data)}```")
            else:
                await interaction.followup.send(f"```No world data available.```")
        elif target == "wind":
            world_data = self.__player_data_agent.get_world_data('wind')
            if world_data:
                wind_direction = self.get_wind_direction(world_data['angle_degrees'])
                await interaction.followup.send(f"```💨 - Current Wind:\n{self.get_wind_description(world_data)}```")
            else:
                await interaction.followup.send(f"```No world data available.```")
        else:
            await interaction.followup.send(f"```No world data for {target}```")
    # end traits_slash

    # # Disabled until a discord-to-pz-username connection can be made
    # @app_commands.command(name="map", description="Show a player's last known location on b42map.com")
    # @app_commands.describe(target="A player name.")
    # async def map_slash(self, interaction: discord.Interaction, target:str): #target2:str=None
    #     await interaction.response.defer(thinking=True)
    #     target_lower = target.lower()
    #     if target_lower in self.__player_data_agent.get_player_data():
    #         url = 'https://b42map.com/?'
    #         player_data = self.__player_data_agent.get_player_data()[target_lower]
    #         url += str(round(player_data['coord_x']))+'x'+str(round(player_data['coord_y']))
    #         await interaction.followup.send(f'`{player_data['username']}\'s last known location is `{url}')
    #     else:
    #         await interaction.followup.send(f'```Could not find a player with the name of {target}```')
    # # end map

    # Discord Admin Only Command
    @app_commands.command(name="position", description="Administrators only; Displays a player's map position.")
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(player="Name of a player (i.e., Pedguin)")
    async def position_slash(self, interaction: discord.Interaction, player:str) -> None:
        await interaction.response.defer(thinking=True, ephemeral=True)
        LOGGER.info(f'Position retrieval attempted by {interaction.user.name} with user id {interaction.user.id} and target "{player}"')
        if len(difflib.get_close_matches(player, self.__player_data_agent.get_player_data().keys())) > 0: # Get closest match of players
            players = self.__player_data_agent.get_player_data()
            matches = difflib.get_close_matches(player, players.keys())
            url = 'https://b42map.com/?'+str(round(players[matches[0]]['coords']['x']))+'x'+str(round(players[matches[0]]['coords']['y']))
            status = "🟢" if matches[0] in [player for player in self.__pz_rcon_agent.get_online_players()] else "🔴"
            await interaction.followup.send(f'```{status} - {matches[0]}\'s last known position:``` {url}')
        else:
            await interaction.followup.send(f'```Could not find player named {player}```')
    # end position_slash

    @app_commands.command(name="lastlog", description="Show a player's last login time")
    @app_commands.describe(player="Player name'.")
    async def lastlog_slash(self, interaction: discord.Interaction, player:str): #target2:str=None
        await interaction.response.defer(thinking=True)
        if len(difflib.get_close_matches(player, self.__player_data_agent.get_player_data().keys())) > 0:
            matches = difflib.get_close_matches(player, self.__player_data_agent.get_player_data().keys())
            player_data = self.__player_data_agent.get_player_data(matches[0])
            status = "🟢" if matches[0] in [pl for pl in self.__pz_rcon_agent.get_online_players()] else "🔴"
            await interaction.followup.send(f'```{status} - {player_data['username']}\'s last login: {datetime.fromtimestamp(round(player_data['lastLogin'])).strftime("%B %d, %Y, %H:%M:%S")}```')
        else:
            await interaction.followup.send(f'```Could not find player named {player}```')
    # end lastlog_slash

    def get_help_description(self) -> str:
        lines = []
        lines.append("📜 **Available Commands:**")
        lines.append("• `/online` — Show currently online players.")
        lines.append("• `/time` — Show top 10 players by playtime.")
        lines.append("• `/time [player]` — Show total playtime for a player.")
        lines.append("• `/survived` — Show top 10 players by survival time.")
        lines.append("• `/survived [player]` — Show total hours survived for a player.")
        lines.append("• `/zombies` — Show top 10 players by zombie kills.")
        lines.append("• `/zombies [player]` — Show total zombie kills for a player.")
        lines.append("• `/skills` — Show top 10 players by total skill levels.")
        lines.append("• `/skills [skill]` — Show top 10 players by a skill.")
        lines.append("• `/skills [player]` — Show a specific players skills.")
        lines.append("• `/lastlog [player]` — Show a player's last log in time.")
        lines.append("• `/world` — Show a world report.")
        lines.append("• `/world [time]` — Show a world report.")
        lines.append("• `/world [season]` — Show a world report.")
        lines.append("• `/world [temperature]` — Show a world report.")
        lines.append("• `/world [weather]` — Show a world report.")
        lines.append("• `/world [wind]` — Show a world report.")
        lines.append("• `/commands` — Show this list.")
        lines.append("• `/help` — Alias for `/commands`")
        return "\n".join(lines)
    # end get_help_description

    @app_commands.command(name="commands", description="Show all available commands")
    async def commands_slash(self, interaction: discord.Interaction):    
        await interaction.response.send_message(self.get_help_description() , ephemeral=True)
    # end commands_slash

    @app_commands.command(name="help", description="Show all available commands")
    async def help_slash(self, interaction: discord.Interaction):    
        await interaction.response.send_message(self.get_help_description() , ephemeral=True)
    # end commands_slash

    # Discord Admin Only Command
    @app_commands.command(name="admincommands", description="Administrators only; Show all available admin commands")
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def adminCommands_slash(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            "📜 **Available Admin Commands:**\n"
            "• `/position [player]` — Show the current position of a player.\n"
            "• `/sync` — Syncs all discord commands.\n"
            "• `/reload [cog_name]` — Reloads a specific cog (i.e., \"core\" or \"pz_stats\").\n"
            "• `/close` — Manually stops the bot. (WARNING: Avoid using unless owner).\n"
            "• `/adminCommands` — Show this list.",
            ephemeral=True
        )
    # end adminCommands_slash

    def get_wind_direction(self, angle_degrees:float, short:bool = False) -> str:
        wind_direction = ""
        if angle_degrees <= 45+22.5 and angle_degrees >= 45-22.5:
            wind_direction = "Northeast" if not short else "NE"
        elif angle_degrees <= 135+22.5 and angle_degrees >= 135-22.5:
            wind_direction = "Northwest" if not short else "NW"
        elif angle_degrees <= 225+22.5 and angle_degrees >= 225-22.5:
            wind_direction = "Southwest" if not short else "SW"
        elif angle_degrees <= 315+22.5 and angle_degrees >= 315-22.5:
            wind_direction = "Southeast" if not short else "SE"
        elif angle_degrees <= 0+22.5 and angle_degrees >= 360-22.5:
            wind_direction = "East" if not short else "E"
        elif angle_degrees <= 90+22.5 and angle_degrees >= 90-22.5:
            wind_direction = "North" if not short else "N"
        elif angle_degrees <= 180+22.5 and angle_degrees >= 180-22.5:
            wind_direction = "West" if not short else "W"
        elif angle_degrees <= 270+22.5 and angle_degrees >= 270-22.5:
            wind_direction = "South" if not short else "S"
        else:
            wind_direction = f"{round(angle_degrees, 1)}°"
        return wind_direction
    # end get_wind_direction

    def get_weather_description(self, weather_data:dict) -> str:
        if weather_data:
            lines = []
            lines.append(f"\tClouds: {round(weather_data['cloud_intensity'], 1)}")
            lines.append(f"\tHumidity: {round(weather_data['humidity'], 1)}")
            lines.append(f"\tFog Intensity: {round(weather_data['fog_intensity'], 1)}")
            if weather_data['thunderstorm']:
                lines.append(f"\tThunderstorming")
            lines.append("\tPrecipitation:")
            if weather_data['precipitation']['raining']:
                lines.append(f"\t\tRain Intensity: {round(weather_data['precipitation']['rain_intensity'], 1)}")
            if weather_data['precipitation']['snowing']:
                lines.append(f"\t\tSnow Intensity: {round(weather_data['precipitation']['snow_intensity'], 1)}")
            if weather_data['precipitation']['snow']:
                lines.append(f"\t\tSnow Strength: {round(weather_data['precipitation']['snow_strength'], 1)}")
            if not weather_data['precipitation']['raining'] and not weather_data['precipitation']['snowing'] and not weather_data['precipitation']['snow']:
                lines.append(f"\t\tNo Precipitation")
            return "\n".join(lines)
        return "Weather data not retrieved."
    # end get_weather_description

    def get_time(self, time_data:dict) -> str:
        if time_data:
            return f"{datetime(year=time_data['year'], month=time_data['month'], day=time_data['day'], hour=time_data['hour'], minute=time_data['minute']).strftime('%B %d, %Y %H:%M')}"
        return "Time data not recieved./"
    # end get_time

    def get_wind_description(self, wind_data:dict) -> str:
        if wind_data:
            lines = []
            lines.append(f"\tSpeed: {round(wind_data['speed_kph'], 1)} km/h")
            wind_direction = self.get_wind_direction(wind_data['angle_degrees'])
            lines.append(f"\tDirection: {wind_direction}")
            lines.append(f"\tIntensity: {round(wind_data['intensity'], 1)}")
            return "\n".join(lines)
        return "Wind data not retrieved."
    # end get_wind_description

    def format_output(self, lines:list[str]) -> str:
        output = ""
        for line in lines:
            if len(output) + len(line) <= 1993:
                output += line
        return "```"+output+"```"
# end Project_Zomboid_Commands

async def setup(bot:Discord_Bot):
    await bot.add_cog(Project_Zomboid_Commands(bot, bot.get_pz_rcon_agent(), bot.get_player_data_agent()))