import discord
from discord import app_commands
from discord.ext import commands
import responses
import nacl
from search import youtube_search
from yt_dlp import YoutubeDL
import argparse
from googleapiclient.discovery import build
import os
from bs4 import BeautifulSoup
#import package to make script wait
import asyncio

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.message_content = True
TOKEN = 'MTEzMTU1OTU3OTQ5NTQ0ODU5Ng.GRrkOF.9XxYeknyj7SVcsQqX2AD2k-5CAIFewCzsZ9a6k'

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

queuePlaylist = []
sourcePlaylist = []
class SimpleView(discord.ui.View):
    @discord.ui.button(label="testtesttesttesttesttesttesttesttesttesttesttesttesttesttest", style=discord.ButtonStyle.secondary, custom_id="test")
    async def hello(self, interaction: discord.Interaction, button: discord.ui.Button, interaction_type: discord.InteractionType):
        await interaction.response.send_message("Hello!", ephemeral=True)

class SearchItem(discord.ui.Button):
    def __init__(self, label, custom_id, style=discord.ButtonStyle.blurple, **kwargs):
        super().__init__(label=label, custom_id=custom_id, style=style, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        await play_audio(f'https://www.youtube.com/watch?v={self.custom_id}',interaction)
        await interaction.edit_original_response(view=None, content=f"Played {self.label}")
        


def build_button(label):
    label = label.split(' (')
    id = label[-1]
    id = id[0:-1]
    label = label[0:-1]
    label = ' '.join(label)
    if len(label) > 80:
        label = label[0:70] + '...'
    # use beatiful soup to turn the unicode html into normal unicode
    soup = BeautifulSoup(label, 'html.parser')
    label = soup.get_text()
    return SearchItem(label=label, custom_id=id)

#plays a song from youtube link
@tree.command(name = "play", description = "Play music from youtube link", guild=discord.Object(id=536041241972834304)) 
async def play(interaction, link : str):
    if len(queuePlaylist) == 0: # First song in the queue
        await interaction.response.defer(ephemeral=False)
        await play_audio(link,interaction)
        queuePlaylist.append(link)
        await interaction.followup.send(responses.get_random_quip())
    else: # There is a song already playing/in queue
        await interaction.response.defer(ephemeral=False)
        queuePlaylist.append(link)
        await interaction.followup.send("Added song to queue!")

# Pause audio that is playing
# TODO: Find way to determine if audio is still being played. If song is over, don't want to allow user to pause a finished song
@tree.command(name = "pause", description = "Pause music that is playing", guild = discord.Object(id=536041241972834304))
async def pause(interaction):
    await interaction.response.defer(ephemeral=False)
    voice = discord.utils.get(client.voice_clients, guild=interaction.guild)
    if voice.is_paused(): # Audio is playing, can be paused
        await interaction.followup.send("You cannot pause music that is already paused!")
    else:
        await pause_audio(interaction)
        await interaction.followup.send(f"Music paused by {interaction.user.mention}")

# Resume audio that is paused
# TODO: Find way to determine if audio is still being played. If song is over, don't want to allow user to resume a finished song
@tree.command(name = "resume", description = "Resume music that is paused", guild = discord.Object(id=536041241972834304))
async def resume(interaction):
    await interaction.response.defer(ephemeral=False)
    voice = discord.utils.get(client.voice_clients, guild=interaction.guild)
    if voice.is_playing():
        await interaction.followup.send("You cannot resume music that is already playing!")
    else:
        await resume_audio(interaction)
        await interaction.followup.send(f"Music resumed by {interaction.user.mention}")

# Skip a song
# TODO: Find way to determine if audio is playing. If no song, dont want user to skip
@tree.command(name = "skip", description = "Skip the current song", guild = discord.Object(id=536041241972834304))
async def skip(interaction):
    await interaction.response.defer(ephemeral=False)
    voice = discord.utils.get(client.voice_clients, guild=interaction.guild)
    await interaction.followup.send(f"Song skipped by {interaction.user.mention}")
    voice.stop()

# Show the queue
# TODO: Have this command work
@tree.command(name = "queue", description = "Shows the current song queue", guild = discord.Object(id=536041241972834304))
async def queue(interaction):
    await interaction.response.defer(ephemeral=False)
    for i in queuePlaylist:
        await interaction.followup.send(f"{str(i+1)}: {queuePlaylist[i]}")

@tree.command(name = "clear", description = "Clears the current queue", guild = discord.Object(id=536041241972834304))
async def clear(interaction):
    await interaction.response.defer(ephemeral=False)
    queuePlaylist.clear()
    sourcePlaylist.clear()
    await interaction.followup.send(f"Queue was cleared by {interaction.user.mention}")

async def send_message(message, user_message, is_private):
    try:
        response = responses.handle_response(user_message)
        await message.author.send(response) if is_private else await message.channel.send(response)
    except Exception as e:
        print(e)

@tree.command(name = "viking_funeral", description = "Send a member a proper fairwell", guild=discord.Object(id=536041241972834304)) 
async def vikingFuneral(interaction, member : discord.Member):
    await interaction.response.defer(ephemeral=False)
    await interaction.followup.send("Fairwell " + member.mention + ". You will be missed.")
    await play_audio("https://www.youtube.com/watch?v=ofm0FXIAq1U", interaction)
    #wait for song to finish
    await asyncio.sleep(156)
    await member.kick()


@tree.command(name = "search", description = "Search for a song on YouTube", guild=discord.Object(id=536041241972834304)) 
async def search(interaction, search : str):
    parser = argparse.ArgumentParser()
    parser.add_argument('--q', help='Search term', default=search)
    parser.add_argument('--max-results', help='Max results', default=10)
    args = parser.parse_args()
    videos = youtube_search(args)
    videos = videos[1]
    videos = videos.split('\n')
    view = discord.ui.View()
    for video in videos:
        view.add_item(build_button(video))
    await interaction.response.send_message(view=view, content='**Here\'s what I found**')

   
@tree.command(name = 'pick', description = "Pick video from search list", guild=discord.Object(id=536041241972834304))
async def pick(interaction, pick : str):
    await play_audio(interaction, f'https://www.youtube.com/watch?v={pick}', False)

@tree.command(name = 'disconnect', description = "Kick V.H.O.S from their current channel", guild=discord.Object(id=536041241972834304))
async def disconnect(interaction):
            await interaction.response.defer(ephemeral=False)
            voice = discord.utils.get(client.voice_clients, guild=interaction.guild)
            if voice.is_connected():
                await voice.disconnect()
                await interaction.followup.send(f"Disconnected by {interaction.user.mention}")
                queuePlaylist.clear()
                sourcePlaylist.clear()
            else:
                await interaction.followup.send("Dumb human, I'm not in a voice channel! (But I'll let you off the hook this time)")
            

# asnyc function to have the bot join voice channel and play audio from youtube
async def play_audio(user_message, message):
    try:
        try:
            os.remove("audio.mp3")
        except:
            pass
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'audio.mp3',
        }
        ydl = YoutubeDL(ydl_opts)
        info = ydl.extract_info(user_message, download=True, process=True, ie_key='Youtube')
        URL = info['formats'][0]['url']

    # check if input link is for a playlist or a single video
        #if '&list=' in user_message:

        voice = discord.utils.get(client.voice_clients, guild=message.guild)
        try:
            channel = message.user.voice.channel
        except:
            return await message.channel.send("You're not in a voice channel, dumbass!")
        if voice == None:
            await channel.connect()
            voice = discord.utils.get(client.voice_clients, guild=message.guild)
        source = discord.FFmpegPCMAudio(executable="C:/PATH_Programs/ffmpeg.exe", source="audio.mp3")
        sourcePlaylist.append(source)
        voice.play(source, after=audioDone)
        voice.is_playing()
    except Exception as e:
        print(e)

# Pause audio if playing
async def pause_audio(message):
    voice = discord.utils.get(client.voice_clients, guild=message.guild)
    try:
        voice.pause()
        voice.is_paused() # Audio is paused
    except Exception as e:
        print(e)

# Resume audio if paused
async def resume_audio(message):
    voice = discord.utils.get(client.voice_clients, guild=message.guild)
    try:
        voice.resume() 
        voice.is_playing() # Audio is playing again
    except Exception as e:
        print(e)

def playNext(user_message):
    try:
        try:
            os.remove("audio.mp3")
        except:
            pass
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'audio.mp3',
        }
        ydl = YoutubeDL(ydl_opts)
        info = ydl.extract_info(user_message, download=True, process=True, ie_key='Youtube')
        URL = info['formats'][0]['url']

    # check if input link is for a playlist or a single video
        #if '&list=' in user_message:
        voice = discord.utils.get(client.voice_clients)
        source = discord.FFmpegPCMAudio(executable="C:/PATH_Programs/ffmpeg.exe", source="audio.mp3")
        sourcePlaylist.append(source)
        voice.play(source, after=audioDone)
        voice.is_playing()
    except Exception as e:
        print(e)

# Used in play(after=) to determine when audio is finished
def audioDone(error):
    try:
        sourcePlaylist[0].cleanup()
        sourcePlaylist.pop(0) # Remove 0th item from sourcePlaylist
        queuePlaylist.pop(0) # Remove 0th item from queuePlaylist
        playNext(queuePlaylist[0])
    except Exception as e:
        print(e)

def run_discord_bot():

    @client.event
    async def on_ready():
        print(f'{client.user} is now running!')
        await tree.sync(guild=discord.Object(id=536041241972834304))
        
        await client.change_presence(activity=discord.Streaming(name='your data off-planet', url='https://www.youtube.com/watch?v=dQw4w9WgXcQ'))
        print("Ready!")

    @client.event
    async def on_message(message):
        # Make sure bot doesn't get stuck in an infinite loop
        if message.author == client.user:
            return print("Bot can't respond to itself!")

        # Get data about the user
        username = str(message.author)
        user_message = str(message.content)
        channel = str(message.channel)

        # Debug printing
        print(f"{username} said: '{user_message}' ({channel})")
        await send_message(message, user_message, is_private=False)

    #play song from selected button 
    @client.event
    async def on_button_click(interaction):
        await interaction.response.defer(ephemeral=False)
        await play_audio(f'https://www.youtube.com/watch?v={interaction.component.custom_id}',interaction)
        await interaction.followup.send(responses.get_random_quip())
    

    client.run(TOKEN)