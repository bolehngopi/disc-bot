import discord
from discord.ext import commands
from discord import app_commands

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping", help="Returns the bot's latency")
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)  # Convert to ms
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Latency: {latency}ms",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
    
    @app_commands.command(name="ping", description="Returns the bot's latency")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)  # Convert to ms
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Latency: {latency}ms",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.command(name="serverinfo", help="Displays information about the server")
    async def serverinfo(self, ctx):
        guild = ctx.guild
        embed = discord.Embed(
            title=f"{guild.name} Server Information",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.add_field(name="Server ID", value=guild.id, inline=True)
        embed.add_field(name="Region", value=guild.region, inline=True)
        embed.add_field(name="Member Count", value=guild.member_count, inline=True)
        embed.add_field(name="Owner", value=guild.owner, inline=True)
        embed.add_field(name="Created At", value=guild.created_at.strftime("%B %d, %Y"), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="userinfo", help="Displays information about a user")
    async def userinfo(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        embed = discord.Embed(
            title=f"User Information - {member.display_name}",
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
        embed.add_field(name="User ID", value=member.id, inline=True)
        embed.add_field(name="Username", value=str(member), inline=True)
        embed.add_field(name="Nickname", value=member.display_name, inline=True)
        embed.add_field(name="Joined Server", value=member.joined_at.strftime("%B %d, %Y"), inline=True)
        embed.add_field(name="Account Created", value=member.created_at.strftime("%B %d, %Y"), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="invite", help="Provides an invite link for the bot")
    async def invite(self, ctx):
        embed = discord.Embed(
            title="Invite Me!",
            description=f"[Click here to invite the bot](https://discord.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=8&scope=bot)",
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed)

    @commands.command(name="help", help="Displays this help message")
    async def help(self, ctx, category: str = None):
        embed = discord.Embed(
            title="Help",
            description="List of available commands",
            color=discord.Color.blurple()
        )
        
        if category:
            cog = self.bot.get_cog(category.capitalize())
            if cog:
                cog_commands = cog.get_commands()
                command_list = ""
                for command in cog_commands:
                    command_list += f"`!{command.name}`: {command.help}\nAliases: `{', '.join(command.aliases)}`\n"
                if command_list:
                    embed.add_field(name=category.capitalize(), value=command_list, inline=False)
            else:
                embed.add_field(name="Error", value=f"Category '{category}' not found", inline=False)
        else:
            for cog in self.bot.cogs:
                cog_commands = self.bot.get_cog(cog).get_commands()
                command_list = ""
                for command in cog_commands:
                    command_list += f"`!{command.name}`: {command.help}\n"
                if command_list:
                    embed.add_field(name=cog, value=command_list, inline=False)

        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)
    
    @commands.command(name="eval", help="Evaluates a Python expression")
    @commands.is_owner()
    async def eval(self, ctx, *, code):
        try:
            result = eval(code)
            await ctx.send(f"```python\n{result}```")
        except Exception as e:
            await ctx.send(f"```python\n{type(e).__name__}: {str(e)}```")
    
    @app_commands.command(name="help", description="Displays this help message")
    async def help_slash(self, interaction: discord.Interaction, category: str = None):
        embed = discord.Embed(
            title="Help",
            description="List of available commands",
            color=discord.Color.blurple()
        )
        
        if category:
            cog = self.bot.get_cog(category.capitalize())
            if cog:
                cog_commands = cog.get_commands()
                command_list = ""
                for command in cog_commands:
                    command_list += f"`!{command.name}`: {command.help}\nAliases: `{', '.join(command.aliases)}`\n"
                if command_list:
                    embed.add_field(name=category.capitalize(), value=command_list, inline=False)
            else:
                embed.add_field(name="Error", value=f"Category '{category}' not found", inline=False)
        else:
            for cog in self.bot.cogs:
                cog_commands = self.bot.get_cog(cog).get_commands()
                command_list = ""
                for command in cog_commands:
                    command_list += f"`!{command.name}`: {command.help}\n"
                if command_list:
                    embed.add_field(name=cog, value=command_list, inline=False)

        await interaction.response.send_message(embed=embed)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if self.bot.user.mentioned_in(message) and message.mention_everyone is False:
            embed = discord.Embed(title="Help", description="My prefix is !\nList of available commands:", color=discord.Color.blue())
            for command in self.bot.commands:
                embed.add_field(name=f"!{command.name}", value=command.help, inline=False)
            await message.channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Utility(bot))
