import discord
from discord.ext import commands
from yt_dlp import YoutubeDL

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.is_playing = False
        self.music_queue = []
        self.current_song = None
        self.YDL_OPTIONS = {
            'format': 'bestaudio/best', 
            'noplaylist': 'True', 
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]
        }
        self.FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 
            'options': '-vn'
        }
        self.vc = None

    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][0]
            except Exception:
                return False
        return {
            'source': info['url'], 
            'title': info['title'], 
            'webpage_url': info['webpage_url'], 
            'duration': info['duration'], 
            'thumbnail': info.get('thumbnail'),
            'description': info.get('description')
        }

    async def play_next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True
            self.current_song = self.music_queue[0][0]

            m_url = self.music_queue[0][0]['source']
            self.music_queue.pop(0)
            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.bot.loop.create_task(self.play_next()))
        else:
            self.is_playing = False
            self.current_song = None

    async def play_music(self, ctx):
        if len(self.music_queue) > 0:
            self.is_playing = True
            self.current_song = self.music_queue[0][0]

            m_url = self.music_queue[0][0]['source']
            
            if self.vc is None or not self.vc.is_connected() or self.vc is None:
                self.vc = await self.music_queue[0][1].connect()
                if self.vc is None:
                    await ctx.send("Could not connect to the voice channel")
                    return
            else:
                await self.vc.move_to(self.music_queue[0][1])
            
            self.music_queue.pop(0)
            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.bot.loop.create_task(self.play_next()))
        else:
            self.is_playing = False
            self.current_song = None

    @commands.command(name="play", help="Plays a selected song from YouTube", aliases=["p"])
    async def play(self, ctx, *args):
        query = " ".join(args)
        
        voice_channel = ctx.author.voice.channel
        if voice_channel is None:
            await ctx.send("Connect to a voice channel!")
        else:
            song = self.search_yt(query)
            if type(song) == type(True):
                embed = discord.Embed(
                    title="Not Found", 
                    description="Could not find the song. Try another keyword.", 
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
            else:
                self.music_queue.append([song, voice_channel])

                if self.is_playing == False:
                    await self.play_music(ctx)
                    embed = discord.Embed(
                        title="Now Playing", 
                        description=f"[{song['title']}]({song['webpage_url']})", 
                        color=discord.Color.random()
                    )
                else:
                    embed = discord.Embed(
                        title="Added to queue", 
                        description=f"[{song['title']}]({song['webpage_url']})", 
                        color=discord.Color.green()
                    )

                embed.set_thumbnail(url=song['thumbnail'])
                embed.add_field(name="Duration", value=f"{song['duration']} seconds", inline=True)
                embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
                await ctx.send(embed=embed)
    
    @commands.command(name="songinfo", help="Displays information about the current song", aliases=["song"])
    async def songinfo(self, ctx):
        if self.current_song:
            song = self.current_song
            embed = discord.Embed(
                title="Song Information",
                description=f"[{song['title']}]({song['webpage_url']})",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=song['thumbnail'])
            embed.add_field(name="Description", value=f"```{song['description']}```", inline=False)
            embed.add_field(name="Duration", value=f"{song['duration']} seconds", inline=True)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Song Information", description="No music playing at the moment", color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.command(name="queue", help="Displays the current songs in queue", aliases=["q"])
    async def queue(self, ctx):
        if self.is_playing or len(self.music_queue) > 0:
            embed = discord.Embed(title="Music Queue", description="", color=discord.Color.orange())
            
            if self.current_song:
                embed.description += f"**Currently Playing:**\n[{self.current_song['title']}]({self.current_song['webpage_url']})\n\n"
                
            if len(self.music_queue) > 0:
                embed.description += "**Up Next:**\n"
                for i in range(len(self.music_queue)):
                    embed.description += f"{i + 1}. [{self.music_queue[i][0]['title']}]({self.music_queue[i][0]['webpage_url']})\n"
            
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Music Queue", description="No music in queue", color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.command(name="skip", help="Skips the current song being played", aliases=["s"])
    async def skip(self, ctx):
        if self.vc is not None and self.vc.is_playing():
            self.vc.stop()
            await self.play_music(ctx)
            await ctx.send("Skipped the current song.")
        else:
            await ctx.send("There is no song playing at the moment.")

    @commands.command(name="stop", help="Stops the music and clears the queue", aliases=["st", "shutup"])
    async def stop(self, ctx):
        self.music_queue = []
        if self.vc is not None:
            self.vc.stop()
            self.is_playing = False
            self.current_song = None
            await self.vc.disconnect()
            await ctx.send("Stopped the music and cleared the queue.")

    @commands.command(name="pause", help="Pauses the music", aliases=["pa"])
    async def pause(self, ctx):
        if self.vc is not None and self.vc.is_playing():
            self.vc.pause()
            await ctx.send("Paused the music.")
        else:
            await ctx.send("The bot is not playing anything at the moment.")

    @commands.command(name="resume", help="Resumes the music", aliases=["r"])
    async def resume(self, ctx):
        if self.vc is not None and self.vc.is_paused():
            self.vc.resume()
            await ctx.send("Resumed the music.")
        else:
            await ctx.send("The bot was not playing anything before this.")

    @commands.command(name="leave", help="Leaves the voice channel", aliases=["disconnect"])
    async def leave(self, ctx):
        self.music_queue = []
        if self.vc is not None:
            await self.vc.disconnect()
            await ctx.send("Left the voice channel.")
    

async def setup(bot):
    await bot.add_cog(Music(bot))
