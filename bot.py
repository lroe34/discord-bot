import discord
from discord import app_commands
from discord.ext import commands
import responses
import nacl
from search import youtube_search
from search import get_youtube_title
from yt_dlp import YoutubeDL
import argparse
from googleapiclient.discovery import build
import os
from bs4 import BeautifulSoup
#import package to make script wait
import asyncio
from pytube import Playlist
import math
import re

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.message_content = True
TOKEN = 'MTEzMTU1OTU3OTQ5NTQ0ODU5Ng.GRrkOF.9XxYeknyj7SVcsQqX2AD2k-5CAIFewCzsZ9a6k'

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

queuePlaylist = [] # Queue of links
source = None      # Used to properly skip a song
titlePlaylist = [] # Queue of titles 
isSong = False     # Used to see if there is a song currently
pageLength = 10    # Page length of the queue display

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

# Plays a song from youtube link
@tree.command(name = "play", description = "Play music from youtube link", guild=discord.Object(id=536041241972834304)) 
async def play(interaction, link : str):
    await interaction.response.defer(ephemeral=False)
    if ("youtube.com" not in link):                              # Not a youtube link
        await interaction.followup.send("Stupid human, that is not a youtube link!")
    else: # Youtube link
        if len(queuePlaylist) == 0:                              # First song in queue
            if ("&list=" in link or "?list=" in link):           # Inserted url is a youtube playlist 
                playlist = Playlist(link)
                for url in playlist:
                    queuePlaylist.append(url)                    # Add link to queue
                    titlePlaylist.append(get_youtube_title(url)) # Add title to queue
                text = responses.get_random_plural_quip() + " Adding " + str(len(playlist.video_urls)) + " songs to queue."
            else:                                                # Not a youtube playlist
                queuePlaylist.append(link)                       # Add link to queue
                titlePlaylist.append(get_youtube_title(link))    # Add title to queue
                text = responses.get_random_quip()
            await interaction.followup.send(text)
            await play_audio(queuePlaylist[0],interaction)
        else:                                                    # There is a song already in queue
            if ("&list=" in link or "?list=" in link):           # Inserted url is a youtube playlist 
                playlist = Playlist(link)
                for url in playlist:
                    queuePlaylist.append(url)                    # Add link to queue
                    titlePlaylist.append(get_youtube_title(url)) # Add title to queue
                text = responses.get_random_plural_quip() + " Adding " + str(len(playlist.video_urls)) + " songs to queue."
            else:                                                # Not a youtube playlist
                queuePlaylist.append(link)                       # Add link to queue
                titlePlaylist.append(get_youtube_title(link))    # Add title to queue
                text = responses.get_random_quip() + " Added song to queue."
            await interaction.followup.send(text)

# Pause audio that is playing
@tree.command(name = "pause", description = "Pause music that is playing", guild = discord.Object(id=536041241972834304))
async def pause(interaction):
    await interaction.response.defer(ephemeral=False)
    voice = discord.utils.get(client.voice_clients, guild=interaction.guild)
    if (not isSong):          # There is no song playing
        await interaction.followup.send("Cannot pause song if there is none!")
    else:                     # Song playing
        if voice.is_paused(): # Audio is paused, cannot pause again
            await interaction.followup.send("You cannot pause music that is already paused!")
        else:                 # Audio is playing, pausing
            await pause_audio(interaction)
            await interaction.followup.send(f"Music paused by {interaction.user.mention}")\


# Resume audio that is paused
@tree.command(name = "resume", description = "Resume music that is paused", guild = discord.Object(id=536041241972834304))
async def resume(interaction):
    await interaction.response.defer(ephemeral=False)
    voice = discord.utils.get(client.voice_clients, guild=interaction.guild)
    if (not isSong):           # There is no song playing
        await interaction.followup.send("Cannot resume a song if there isn't one!")
    else:                      # Song playing
        if voice.is_playing(): # Audio is playing, cannot resume again
            await interaction.followup.send("You cannot resume music that is already playing!")
        else:                  # Audio is paused, resuming
            await resume_audio(interaction)
            await interaction.followup.send(f"Music resumed by {interaction.user.mention}")

# Skip a song
@tree.command(name = "skip", description = "Skip the current song", guild = discord.Object(id=536041241972834304))
async def skip(interaction):
    await interaction.response.defer(ephemeral=False)
    voice = discord.utils.get(client.voice_clients, guild=interaction.guild)
    if (not isSong): # There is no song playing
        await interaction.followup.send("Cannot skip a song if there is none!")
    else:            # Song playing
        await interaction.followup.send(f"Song skipped by {interaction.user.mention}")
        voice.stop() # Skip song

# Show the current queue
@tree.command(name = "queue", description = "Shows the current song queue", guild = discord.Object(id=536041241972834304))
async def queue(interaction, page : int = 1):
    await interaction.response.defer(ephemeral=False)
    if (len(queuePlaylist) == 0):                          # No songs in queue
        await interaction.followup.send("Queue is empty!")
    else:                                                  # Songs in queue
        pages = math.ceil(len(queuePlaylist) / pageLength) # How many pages are needed to display the whole queue depending on what the page length is
        if page > pages:                                   # Cannot have a page selection greater than the total pages
            page = pages
        view = "**Current queue (Page " + str(page) + " of " + str(pages) + "):**\n"
        queuePos = 1 + ((int(page) - 1) * pageLength)
        for i in range(queuePos, queuePos + pageLength):   # Loop through playlist and add them to view
            if (int(queuePos) - 1) < (int(page) * pageLength):
                if (int(i) <= len(titlePlaylist)):
                    view += str(queuePos) + ": " +  str(titlePlaylist[i-1]) + "\n"
                    queuePos += 1
        view += "\n**Page length:** " + str(pageLength) + " - **Queue length:** " + str(len(queuePlaylist))
        await interaction.followup.send(view)

# Remove a song from the queue
@tree.command(name = "remove", description = "Remove song(s) from the queue using their position", guild = discord.Object(id=536041241972834304))
async def remove(interaction, index : str):
    await interaction.response.defer(ephemeral=False)
    if ("-" in index):                                              # User removing range of indeces
        index = index.replace(" ", "")                              # Remove spaces so format is x-x
        firstIndex = index.split("-")[0]                            # Number before dash
        secondIndex = index.split("-")[1]                           # Number after dash
        if (not firstIndex.isdigit() or not secondIndex.isdigit()): # 1st or 2nd input is not a digit
            await interaction.followup.send("Input for positions must be digits!") 
        if (int(secondIndex) >= len(queuePlaylist)):                # 2nd number is out of index range
            await interaction.followup.send("Cannot remove a song at position " + secondIndex) 
        else:
            if (int(firstIndex) <= 1):                              # Cannot remove song currently playing (index 1) or below
                await interaction.followup.send("Cannot remove a song at position " + firstIndex)
            else:                               
                indexRemove = int(firstIndex)
                while(indexRemove <= int(secondIndex)):             # Iterate through the queue and remove index from queue
                    queuePlaylist.pop(int(firstIndex) - 1)          # Remove link from queue    
                    titlePlaylist.pop(int(firstIndex) - 1)          # Remove title from queue
                    indexRemove += 1
                await interaction.followup.send("Removed songs at positions " + firstIndex + " to " + secondIndex)
    else:                                                           # User removing only one index
        if (int(index) <= 1 or int(index) > len(queuePlaylist)):    # Cannot remove song currently playing (index 1) or below
            await interaction.followup.send("Cannot remove a song at position " + index)
        elif (int(index) > len(queuePlaylist)):                     # Cannot remove song if position is greater than the length of the queue
            await interaction.followup.send("Cannot remove a song at position " + index)
        else:                                                       # Remove index from queue                                   
            queuePlaylist.pop(int(index) - 1)                       # Remove link from queue
            titlePlaylist.pop(int(index) - 1)                       # Remove title from queue
            await interaction.followup.send("Removed song at position " + index)

# Change the page length when calling queue command
@tree.command(name = "queue_length", description = "Change the length of the queue display", guild = discord.Object(id=536041241972834304))
async def queueLength(interaction, queuelength : int):
    await interaction.response.defer(ephemeral=False)
    if (queuelength < 1):        # Queue display length cannot be less than 1
        await interaction.followup.send("Stupid fleshy human! Queue length has to be greater than 0!")
    else:                        # Queue display length is good length
        global pageLength 
        pageLength = queuelength # Change global pageLength  
        await interaction.followup.send(f"Queue page length changed to {pageLength}")

# Show the current song that is playing
@tree.command(name = "current", description = "Shows the current song playing", guild = discord.Object(id=536041241972834304))
async def current(interaction):
    await interaction.response.defer(ephemeral=False)
    if (len(queuePlaylist) == 0):                                          # There is no song playing
        await interaction.followup.send(f"There is no song playing!")
    else:                                                                  # There is a song playing
        currentSong = str(titlePlaylist[0]) + "\n" + str(queuePlaylist[0]) # Print the song title and youtube link
        await interaction.followup.send(f"Current song that is playing: {currentSong}")

# Clear the whole queue
@tree.command(name = "clear", description = "Clears the current queue", guild = discord.Object(id=536041241972834304))
async def clear(interaction):
    await interaction.response.defer(ephemeral=False)
    if (len(queuePlaylist) == 0): # There is no queue to clear
        await interaction.followup.send("Silly human! There is already no queue!")
    else:                         # There is a queue
        clearQueue()                  # Clear the queue
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
    if (len(queuePlaylist) == 0): # There is no song in queue
        await play_audio(interaction, f'https://www.youtube.com/watch?v={pick}', False)
    else:                         # There are song(s) in queue
        queuePlaylist.append(f"https://www.youtube.com/watch?v={pick}")                     # Add link to queue
        titlePlaylist.append(get_youtube_title(f"https://www.youtube.com/watch?v={pick}"))  # Add title to queue

# Disconnect bot from voice channel
@tree.command(name = 'disconnect', description = "Kick V.H.O.S from their current channel", guild=discord.Object(id=536041241972834304))
async def disconnect(interaction):
    await interaction.response.defer(ephemeral=False)
    voice = discord.utils.get(client.voice_clients, guild=interaction.guild)
    if voice.is_connected():     # Bot is in voice channel
        await voice.disconnect() # Disconnect the bot
        await interaction.followup.send(f"Disconnected by {interaction.user.mention}")
        global isSong
        isSong = False           # There is no song available
        clearQueue()             # Clear the queue
    else:                        # Bot is no in voice channel
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
        voice = discord.utils.get(client.voice_clients, guild=message.guild)
        try:
            channel = message.user.voice.channel
        except:                             # User not in a voice channel
            clearQueue()                    # Clear what was just added since not in voice channel
            return await message.channel.send("You're not in a voice channel, dumbass!")
        if voice == None:                   # Bot not in voice channel, join voic channel
            await channel.connect()
            voice = discord.utils.get(client.voice_clients, guild=message.guild)
        global source
        source = discord.FFmpegPCMAudio(executable="C:/PATH_Programs/ffmpeg.exe", source="audio.mp3")
        global isSong
        isSong = True                       # There is a song available
        voice.play(source, after=audioDone) # Play the song
        voice.is_playing()                  # Song is playing
    except Exception as e:
        print(e)

# Pause audio if playing
async def pause_audio(message):
    voice = discord.utils.get(client.voice_clients, guild=message.guild)
    try:                  
        voice.pause()     # Pause audio
        voice.is_paused() # Audio is paused
    except Exception as e:
        print(e)

# Resume audio if paused
async def resume_audio(message):
    voice = discord.utils.get(client.voice_clients, guild=message.guild)
    try:
        voice.resume()     # Resume audio
        voice.is_playing() # Audio is playing again
    except Exception as e:
        print(e)

# Clear both title queue and link queue
def clearQueue():
    queuePlaylist.clear() # Clear link queue
    titlePlaylist.clear() # Clear title queue

# Play the next song in the queue
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

        voice = discord.utils.get(client.voice_clients)
        global source
        source = discord.FFmpegPCMAudio(executable="C:/PATH_Programs/ffmpeg.exe", source="audio.mp3")
        global isSong 
        isSong = True                       # There is a song available
        voice.play(source, after=audioDone) # Play the song
        voice.is_playing()                  # Song is playing
    except Exception as e:
        print(e)

# Used in play(after=) to determine when audio is finished
def audioDone(error):
    try:
        global source
        global isSong
        isSong = False             # There is no longer a song available
        source.cleanup()           # Cleanup the source to skip properly
        queuePlaylist.pop(0)       # Remove 0th item from link queue
        titlePlaylist.pop(0)       # Remove 0th item from title queue
        playNext(queuePlaylist[0]) # Play the next song in queue
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