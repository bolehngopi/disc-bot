import discord
from discord.ext import commands, tasks
import asyncio
import os
from prettytable import PrettyTable
from colorama import Fore, Style, init
from itertools import cycle
import datetime

# Initialize colorama
init()

TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = 796177609544826951

intents = discord.Intents.all()

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

bot_status = cycle(['with commands', 'with the API', 'with the code', 'with the database'])

@tasks.loop(seconds=10)
async def change_status():
    await bot.change_presence(activity=discord.Game(next(bot_status)))

@change_status.before_loop
async def before_change_status():
    await bot.wait_until_ready()

@bot.event
async def on_ready():
    print(f"/{'='*50}\\")
    print(f"| Logged in as {Fore.RED}{bot.user.name}{Style.RESET_ALL} ({bot.user.id}) |")
    try:
        synced = await bot.tree.sync()
        print(f"{Fore.GREEN}Synced {len(synced)} command(s).{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Failed to sync commands: {e}{Style.RESET_ALL}")
    print(f"\\{'='*50}/")
    
    # Send a message to the channel ID when the bot is ready
    channel = bot.get_channel(CHANNEL_ID)
    await channel.send('Bot is ready!')

async def load_cogs():
    print('Loading cogs...')
    
    loaded_files = []
    loaded_commands = []
    error = []
    
    for root, dirs, files in os.walk('./commands'):
        for filename in files:
            if filename.endswith('.py'):
                module_path = os.path.join(root, filename).replace('./', '').replace('\\', '.').replace('/', '.')
                module_path = module_path[:-3]
                if module_path in bot.extensions:
                    loaded_files.append((module_path, "Already Loaded"))
                    continue
                try:
                    await bot.load_extension(module_path)
                    loaded_files.append((module_path, "Success"))
                except Exception as e:
                    error.append((module_path, e))
                    loaded_files.append((module_path, f"Failed"))

    # Check for individual commands in loaded cogs
    for cog_name in bot.cogs:
        cog = bot.get_cog(cog_name)
        for command in cog.get_commands():
            if bot.get_command(command.name):
                status = "Already Loaded"
            else:
                status = "Success"
            loaded_commands.append((f"{cog_name}.{command.name}", status))

    table = PrettyTable()
    table.field_names = [f"{Fore.GREEN}Loaded Cogs{Style.RESET_ALL}", f"{Fore.GREEN}Status{Style.RESET_ALL}"]
    for file, status in loaded_files:
        status_color = Fore.GREEN if "Success" in status else Fore.RED if "Failed" in status else Fore.YELLOW
        table.add_row([f"{Fore.CYAN}{file}{Style.RESET_ALL}", f"{status_color}{status}{Style.RESET_ALL}"])
    
    table.add_row(["", ""], divider=True)
    table.add_row([f"{Fore.GREEN}Loaded Commands{Style.RESET_ALL}", f"{Fore.GREEN}Status{Style.RESET_ALL}"], divider=True)
    for file, status in loaded_commands:
        status_color = Fore.GREEN if "Success" in status else Fore.RED if "Failed" in status else Fore.YELLOW
        table.add_row([f"{Fore.CYAN}{file}{Style.RESET_ALL}", f"{status_color}{status}{Style.RESET_ALL}"])
    
    print(table)
    
    for file, e in error:
        print(f"{Fore.CYAN}{file}{Style.RESET_ALL}: {Fore.RED}{e}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Cogs and Commands loaded. {datetime.datetime.now()}{Style.RESET_ALL}")

async def main() -> None:
    async with bot:
        await load_cogs()
        change_status.start()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
