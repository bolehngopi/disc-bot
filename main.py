import discord
from discord.ext import commands
import os
from prettytable import PrettyTable
from colorama import Fore, Style, init
import datetime

# Initialize colorama
init()

TOKEN = os.getenv('DISCORD_TOKEN')
GENIUS_API_TOKEN = os.getenv('GENIUS_API_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)  # Disable default help command

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('Loading cogs...')
    
    #send to a channel using channel ID
    channel = bot.get_channel(796177609544826951)
    await channel.send("Bot is online")
    
    loaded_files = []
    
    for root, dirs, files in os.walk('./commands'):
        for filename in files:
            if filename.endswith('.py'):
                # Construct the module path
                module_path = os.path.join(root, filename).replace('./', '').replace('\\', '.').replace('/', '.')
                module_path = module_path[:-3]  # Remove the .py extension
                try:
                    await bot.load_extension(module_path)
                    loaded_files.append((module_path, "Success"))
                except Exception as e:
                    loaded_files.append((module_path, f"Failed: {e}"))
    
    # Print the loaded files in a table with color
    table = PrettyTable()
    table.field_names = [f"{Fore.GREEN}Loaded Cogs{Style.RESET_ALL}", f"{Fore.GREEN}Status{Style.RESET_ALL}"]
    for file, status in loaded_files:
        status_color = Fore.GREEN if "Success" in status else Fore.RED
        table.add_row([f"{Fore.CYAN}{file}{Style.RESET_ALL}", f"{status_color}{status}{Style.RESET_ALL}"])
    
    print(table)
    #Add timestamp to the print statement
    print(f"{Fore.GREEN}Cogs loaded. {datetime.datetime.now()}{Style.RESET_ALL}")

    # Set bot activity status change every 5 minute in given array
    activity = discord.Game(name=f"!help | {len(bot.guilds)} servers")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    raise error

bot.run(TOKEN)
