import discord
from discord.ext import commands
from yt_dlp import YoutubeDL
import asyncio
import aiohttp

class MusicControlView(discord.ui.View):
    def __init__(self, music_cog, ctx):
        super().__init__(timeout=None)
        self.music_cog = music_cog
        self.ctx = ctx

    @discord.ui.button(label="Pause", style=discord.ButtonStyle.primary)
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.music_cog.pause(self.ctx)

    @discord.ui.button(label="Resume", style=discord.ButtonStyle.primary)
    async def resume_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.music_cog.resume(self.ctx)

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.primary)
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.music_cog.skip(self.ctx)

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.music_cog.stop(self.ctx)

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
        self.vc: discord.VoiceClient = None
        self.inactivity_timer = None

    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(f"ytsearch:{item}", download=False)['entries'][0]
            except Exception as e:
                print(f"Error searching YouTube: {e}")
                return False
        return {
            'source': info['url'],
            'title': info['title'],
            'webpage_url': info['webpage_url'],
            'duration': info['duration'],
            'thumbnail': info.get('thumbnail'),
            'description': info.get('description'),
            'artist': info.get('artist', 'Unknown')
        }

    def extract_info(self, url):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except Exception as e:
                print(f"Error extracting info: {e}")
                return False
        return {
            'source': info['url'],
            'title': info['title'],
            'webpage_url': info['webpage_url'],
            'duration': info['duration'],
            'thumbnail': info.get('thumbnail'),
            'description': info.get('description'),
            'artist': info.get('artist', 'Unknown')
        }

    async def play_next(self, ctx):
        if self.music_queue:
            self.is_playing = True
            self.current_song = self.music_queue.pop(0)[0]
            m_url = self.current_song['source']

            def after_playing(error):
                if error:
                    print(f"Error after playing: {error}")
                asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop)

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=after_playing)

            embed = discord.Embed(
                title="Now Playing",
                description=f"[{self.current_song['title']}]({self.current_song['webpage_url']})",
                color=discord.Color.random()
            )
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
            await ctx.send(embed=embed, delete_after=self.current_song['duration'], view=MusicControlView(self, ctx))
        else:
            self.is_playing = False
            self.current_song = None
            await self.start_inactivity_timer(ctx)

    async def play_music(self, ctx):
        if self.music_queue:
            self.is_playing = True
            self.current_song = self.music_queue[0][0]
            m_url = self.current_song['source']

            if not self.vc or not self.vc.is_connected():
                try:
                    self.vc = await self.music_queue[0][1].connect()
                except Exception as e:
                    print(f"Error connecting to voice channel: {e}")
                    await ctx.send("Could not connect to the voice channel")
                    return
            else:
                await self.vc.move_to(self.music_queue[0][1])

            self.music_queue.pop(0)
            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
        else:
            self.is_playing = False
            self.current_song = None
            await self.start_inactivity_timer(ctx)

    async def start_inactivity_timer(self, ctx):
        if self.inactivity_timer:
            self.inactivity_timer.cancel()

        self.inactivity_timer = self.bot.loop.create_task(self.inactivity_check(ctx))

    async def inactivity_check(self, ctx: commands.Context):
        await asyncio.sleep(300)  # Wait for 5 minutes
        if not self.is_playing and not self.music_queue:
            embed = discord.Embed(
                title="Inactivity",
                description="No music in queue for 5 minutes, disconnecting...",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=10)
            await self.leave(ctx)

    @commands.command(name="play", help="Plays a selected song from YouTube", aliases=["p"])
    async def play(self, ctx, *args):
        query = " ".join(args)
        voice_channel = ctx.author.voice.channel
        if not voice_channel:
            await ctx.send("Connect to a voice channel!")
            return

        if query.startswith("http://") or query.startswith("https://"):
            song = self.extract_info(query)
        else:
            song = self.search_yt(query)
        
        if not song:
            embed = discord.Embed(
                title="Not Found",
                description="Could not find the song. Try another keyword or URL.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        self.music_queue.append([song, voice_channel])

        if not self.is_playing:
            await self.play_music(ctx)

        embed = discord.Embed(
            title="Now Playing" if not self.is_playing else "Added to queue",
            description=f"[{song['title']}]({song['webpage_url']})",
            color=discord.Color.random() if not self.is_playing else discord.Color.green()
        )
        embed.set_thumbnail(url=song['thumbnail'])
        embed.add_field(name="Duration", value=f"{song['duration']} seconds", inline=True)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed, view=MusicControlView(self, ctx))

        await self.start_inactivity_timer(ctx)

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
        if self.is_playing or self.music_queue:
            embed = discord.Embed(title="Music Queue", color=discord.Color.orange())

            if self.current_song:
                embed.description = f"**Currently Playing:**\n[{self.current_song['title']}]({self.current_song['webpage_url']})\n\n"

            if self.music_queue:
                embed.description += "**Up Next:**\n"
                for i, song in enumerate(self.music_queue):
                    embed.description += f"{i + 1}. [{song[0]['title']}]({song[0]['webpage_url']})\n"

            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Music Queue", description="No music in queue", color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.command(name="skip", help="Skips the current song being played", aliases=["s"])
    async def skip(self, ctx):
        if self.vc and self.vc.is_playing():
            self.vc.stop()
            await self.play_music(ctx)
            await ctx.send("Skipped the current song.")
        else:
            await ctx.send("There is no song playing at the moment.")

    @commands.command(name="stop", help="Stops the music and clears the queue", aliases=["st", "shutup"])
    async def stop(self, ctx):
        self.music_queue = []
        if self.vc:
            self.vc.stop()
            self.is_playing = False
            self.current_song = None
            await self.vc.disconnect()  
            await ctx.send("Stopped the music and cleared the queue.")
            if self.inactivity_timer:
                self.inactivity_timer.cancel()
                self.inactivity_timer = None

    @commands.command(name="pause", help="Pauses the music", aliases=["pa"])
    async def pause(self, ctx):
        if self.vc and self.vc.is_playing():
            self.vc.pause()
            await ctx.send("Paused the music.")
        else:
            await ctx.send("The bot is not playing anything at the moment.")

    @commands.command(name="resume", help="Resumes the music", aliases=["r"])
    async def resume(self, ctx):
        if self.vc and self.vc.is_paused():
            self.vc.resume()
            await ctx.send("Resumed the music.")
        else:
            await ctx.send("The bot was not playing anything before this.")
            
    @commands.command(name="repeat", help="Repeats the current song", aliases=["re"])
    async def repeat(self, ctx):
        if self.current_song:
            self.music_queue.insert(0, [self.current_song, ctx.author.voice.channel])
            await ctx.send("Repeated the current song.")
        else:
            await ctx.send("No song to repeat.")

    @commands.command(name="leave", help="Leaves the voice channel", aliases=["disconnect"])
    async def leave(self, ctx):
        self.music_queue = []
        if self.vc:
            await self.vc.disconnect()
            await ctx.send("Left the voice channel.")
            if self.inactivity_timer:
                self.inactivity_timer.cancel()
                self.inactivity_timer = None

    @commands.command(name="lyrics", help="Fetches lyrics for the current song", aliases=["ly"])
    async def lyrics(self, ctx):
        if not self.current_song:
            await ctx.send("No song is currently playing.")
            return

        title = self.current_song['title']
        artist = self.current_song['artist']
        if artist and artist != 'Unknown':
            query = f"{title}/{artist}"
        else:
            query = title

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"https://lyrist.vercel.app/api/{query}") as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'lyrics' in data and data['lyrics']:
                            embed = discord.Embed(
                                title=f"Lyrics for {data['title']}",
                                description=data['lyrics'],
                                color=discord.Color.green()
                            )
                            embed.set_thumbnail(url=data.get('image', ''))
                            await ctx.send(embed=embed)
                        else:
                            await ctx.send("Lyrics not found.")
                    else:
                        await ctx.send("Error fetching lyrics. Please try again later.")
            except Exception as e:
                await ctx.send(f"An error occurred while fetching lyrics: {e}")

async def setup(bot):
    await bot.add_cog(Music(bot))
