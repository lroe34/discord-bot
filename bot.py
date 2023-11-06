import discord
from discord import app_commands, Color
from discord.ext import commands
import responses
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
import threading
import random
import sys
import os
from discord.ext import commands
import sys
import os
from discord.ext import commands

from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv("API_KEY")

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

queuePlaylist = [] # Queue of links
titlePlaylist = [] # Queue of titles
source = None      # Used to properly skip a song
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
        t1 = threading.Thread(target=addTitle, args=(f'https://www.youtube.com/watch?v={self.custom_id}',))
        t1.start()
        if (len(queuePlaylist) == 0):
            queuePlaylist.append(f'https://www.youtube.com/watch?v={self.custom_id}')
            await play_audio(f'https://www.youtube.com/watch?v={self.custom_id}',interaction)
            await interaction.edit_original_response(view=None, content=f"Played {self.label}")
        else:
            queuePlaylist.append(f'https://www.youtube.com/watch?v={self.custom_id}')
            await interaction.edit_original_response(view=None, content=f"Added {self.label} to queue")
        
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

# <----- Commands ------>

# Plays a song from youtube link
@tree.command(name = "play", description = "Play music from youtube link", guild=discord.Object(id=536041241972834304)) 
async def play(interaction, link : str):
    await interaction.response.defer(ephemeral=False)
    if ("youtube.com" not in link):                              # Not a youtube link
        await interaction.followup.send("Stupid human, that is not a youtube link!")
    else: # Youtube link
        t1 = threading.Thread(target=addTitle, args=(link,))     # Threading to add title to playlist and start playing song right away
        t1.start()
        if len(queuePlaylist) == 0:                              # First song in queue
            if ("&list=" in link or "?list=" in link):           # Inserted url is a youtube playlist 
                playlist = Playlist(link)
                for url in playlist:
                    queuePlaylist.append(url)                    # Add link to queue
                text = responses.get_random_plural_quip() + " Adding " + str(len(playlist.video_urls)) + " songs to queue."
            else:                                                # Not a youtube playlist
                queuePlaylist.append(link)                       # Add link to queue
                text = responses.get_random_quip()
            await interaction.followup.send(text)
            await play_audio(queuePlaylist[0],interaction)
        else:                                                    # There is a song already in queue                                                 
            if ("&list=" in link or "?list=" in link):           # Inserted url is a youtube playlist 
                playlist = Playlist(link)
                for url in playlist:
                    queuePlaylist.append(url)                    # Add link to queue
                text = responses.get_random_plural_quip() + " Adding " + str(len(playlist.video_urls)) + " songs to queue."
            else:                                                # Not a youtube playlist
                queuePlaylist.append(link)                       # Add link to queue
                text = responses.get_random_quip() + " Added song to queue."
            await interaction.followup.send(text)

# Pause audio that is playing
@tree.command(name = "pause", description = "Pause music that is playing", guild = discord.Object(id=536041241972834304))
async def pause(interaction):
    await interaction.response.defer(ephemeral=False)
    voice = discord.utils.get(client.voice_clients, guild=interaction.guild)
    if (not voice.is_playing() and not voice.is_paused()): # There is no song
        await interaction.followup.send("Cannot pause song if there is none!")
    else:                                                  # Song playing
        if voice.is_paused():                              # Audio is paused, cannot pause again
            await interaction.followup.send("You cannot pause music that is already paused!")
        else:                                              # Audio is playing, pausing
            await pause_audio(interaction)
            msg = await interaction.followup.send(f"Music paused by {interaction.user.mention}")
            await msg.add_reaction("\U000025B6")           # Resume button reaction
            
# Resume audio that is paused
@tree.command(name = "resume", description = "Resume music that is paused", guild = discord.Object(id=536041241972834304))
async def resume(interaction):
    await interaction.response.defer(ephemeral=False)
    voice = discord.utils.get(client.voice_clients, guild=interaction.guild)
    if (not voice.is_playing() and not voice.is_paused()): # There is no song
        await interaction.followup.send("Cannot resume a song if there is none!")
    else:                                                  # Song playing
        if voice.is_playing():                             # Audio is playing, cannot resume again
            await interaction.followup.send("You cannot resume music that is already playing!")
        else:                                              # Audio is paused, resuming
            await resume_audio(interaction)
            msg = await interaction.followup.send(f"Music resumed by {interaction.user.mention}")
            await msg.add_reaction("\U000023F8")           # Pause button reaction

# Skip a song
@tree.command(name = "skip", description = "Skip the current song", guild = discord.Object(id=536041241972834304))
async def skip(interaction):
    await interaction.response.defer(ephemeral=False)
    voice = discord.utils.get(client.voice_clients, guild=interaction.guild)
    if (not voice.is_playing() and not voice.is_paused()): # There is no song 
        await interaction.followup.send("Cannot skip a song if there is none!")
    else:                                                  # Song playing
        await interaction.followup.send(f"Song skipped by {interaction.user.mention}")
        voice.stop()                                       # Skip song

# Show the current queue
@tree.command(name = "queue", description = "Shows the current song queue", guild = discord.Object(id=536041241972834304))
async def queue(interaction, page : int = 1):
    global pageNum
    await interaction.response.defer(ephemeral=False)
    if (len(queuePlaylist) == 0):                          # No songs in queue
        await interaction.followup.send("Queue is empty!")
    else:                                                  # Songs in queue
        pageNum = page
        pages = math.ceil(len(queuePlaylist) / pageLength) # How many pages are needed to display the whole queue depending on what the page length is
        view = await get_queue(page)
        msg = await interaction.followup.send(view)
        if (page == 1):
            await msg.add_reaction("\U000023E9")           # Right arrow to go to next page
        elif (page == pages):
            await msg.add_reaction("\U000023EA")           # Left arrow to go to previous page
        else:
            await msg.add_reaction("\U000025B6")           # Right arrow to go to next page
            await msg.add_reaction("\U000025C0")           # Left arrow to go to previous page
        await msg.add_reaction("\U00002B06")               # Up arrow to increase queueLength
        await msg.add_reaction("\U00002B07")               # Down arrow to decrease queueLength

# Remove a song from the queue
@tree.command(name = "remove", description = "Remove song(s) from the queue using their position", guild = discord.Object(id=536041241972834304))
async def remove(interaction, index : str):
    await interaction.response.defer(ephemeral=False)
    if ("-" in index):                                              # Removing range of indeces
        index = index.replace(" ", "")                              # Remove spaces so format is x-x
        firstIndex = index.split("-")[0]                            # Number before dash
        secondIndex = index.split("-")[1]                           # Number after dash
        if (not firstIndex.isdigit() or not secondIndex.isdigit()): # 1st or 2nd input is not a digit
            await interaction.followup.send("Input for positions must be numbers!") 
        elif (int(secondIndex) > len(queuePlaylist)):               # 2nd number is out of index range
            await interaction.followup.send("Cannot remove a song at position " + secondIndex) 
        elif (int(firstIndex) > int(secondIndex)):
            await interaction.followup.send("Please make the second number larger!")
        else:
            if (int(firstIndex) <= 1):                              # Cannot remove song currently playing (index 1) or below
                await interaction.followup.send("Cannot remove a song at position " + firstIndex)
            else:                               
                indexRemove = int(firstIndex)
                while(indexRemove <= int(secondIndex)):             # Iterate through the queue and remove index from queue
                    queuePlaylist.pop(int(firstIndex) - 1)          # Remove link from queue    
                    titlePlaylist.pop(int(firstIndex) - 1)
                    indexRemove += 1
                await interaction.followup.send("Removed songs at positions " + firstIndex + " to " + secondIndex)
    else:                                                           # User removing only one index
        if (int(index) <= 1 or int(index) > len(queuePlaylist)):    # Cannot remove song currently playing (index 1) or below
            await interaction.followup.send("Cannot remove a song at position " + index)
        elif (not index.isdigit()):
            await interaction.followup.send("Input for position must be a number!")
        else:                                                       # Remove index from queue                                   
            queuePlaylist.pop(int(index) - 1)                       # Remove link from queue
            titlePlaylist.pop(int(index) - 1)
            await interaction.followup.send("Removed song at position " + index)

# # Insert url next in queue
# @tree.command(name = "next", description = "Put song into the next position of the queue", guild = discord.Object(id=536041241972834304))
# async def next(interaction, link : str):
#     await interaction.response.defer(ephemeral=False)
#     if ("youtube.com" not in link):                                        # Not a youtube link
#         await interaction.followup.send("Stupid human, that is not a youtube link!")
#     else: # Youtube link
#         if len(queuePlaylist) == 0:                                        # There is no current song
#             await interaction.followup.send("Idiot! Can't put anything next if there is nothing playing!")
#         else:                                                              # There is a song already in queue
#             if ("&list=" in link or "?list=" in link):                     # Inserted url is a youtube playlist 
#                 playlist = Playlist(link)
#                 position = 1
#                 for url in playlist:
#                     queuePlaylist.insert(position, url)                    # Add link to queue
#                     position += 1
#                 text = responses.get_random_plural_quip() + " Adding " + str(len(playlist.video_urls)) + " songs to queue."
#             else:                                                          # Not a youtube playlist
#                 queuePlaylist.insert(1, link)                              # Add link to queue
#                 text = responses.get_random_quip() + " Added song to queue."
#             await interaction.followup.send(text)

# Replay the current song
@tree.command(name = "replay", description = "Replay the current song next", guild =discord.Object(id=536041241972834304))
async def replay(interaction):
    await interaction.response.defer(ephemeral=False)
    titlePlaylist.insert(1, titlePlaylist[0])
    queuePlaylist.insert(1, queuePlaylist[0])
    await interaction.followup.send(titlePlaylist[0] + " will be replayed next.")

# Move a song based on position
@tree.command(name = "move", description = "Move song(s) based on their old and new position", guild = discord.Object(id=536041241972834304))
async def move(interaction, old_position : str, new_position : str):
    await interaction.response.defer(ephemeral=False)
    old_position = old_position.replace(" ", "") # Remove spaces
    new_position = new_position.replace(" ", "") # Remove spaces
    if ("-" in old_position):                    # Range of indeces
        if ("-" not in new_position):
            await interaction.followup.send("Both positions must be ranges!")
        else:
            old_position1 = old_position.split("-")[0]                            # Old number before dash
            old_position2 = old_position.split("-")[1]                            # Old number after dash
            new_position1 = new_position.split("-")[0]                            # New number before dash
            new_position2 = new_position.split("-")[1]                            # New number after dash
            if (not old_position1.isdigit() or not old_position2.isdigit()        # The inputs on either side of the dashes are not digits
                  or not new_position1.isdigit() or not new_position2.isdigit()):
                await interaction.followup.send("Positions must be digits!")
            elif (int(old_position1) <= 1                                         # old_position1 out of range
                   or int(old_position1) > len(queuePlaylist)):
                await interaction.followup.send("Cannot move song at position " + old_position1)
            elif (int(old_position2) <= 1                                         # old_position2 out of range
                   or int(old_position2) > len(queuePlaylist)):
                await interaction.followup.send("Cannot move song at position " + old_position2)
            elif (int(new_position1) <= 1                                         # new_position1 out of range
                   or int(new_position1) > len(queuePlaylist)):
                await interaction.followup.send("Cannot move song to position " + new_position1)
            elif (int(new_position2) <= 1                                         # new_position2 out of range
                   or int(new_position2) > len(queuePlaylist)):
                await interaction.followup.send("Cannot move song to position " + new_position2)
            elif (int(old_position1) > int(old_position2)                         # 2nd number is smaller than the 1st
                   or int(new_position1) > int(new_position2)):  
                await interaction.followup.send("Please make the second number larger!")
            elif ((int(old_position2) - int(old_position1))                       # The ranges are not the same size
                   != (int(new_position2) - int(new_position1))):
                await interaction.followup.send("The ranges for the old "
                                                + "and new positions have to be the same size!")
            elif (int(old_position1) == int(new_position1)
                   and int(old_position2) == int(new_position2)):
                await interaction.followup.send("The songs are already in those position!")
            elif (int(old_position1) == int(old_position2)
                   or int(new_position1) == int(new_position2)):
                await interaction.followup.send("That is not a range silly!")
            else:               # Both inputs are good
                songLinks = []  # Temp list to store links
                songTitles = [] # Temp list to store titles
                i = int(old_position1)
                while (i <= int(old_position2)): 
                    songLinks.append(queuePlaylist[int(old_position1) - 1])
                    songTitles.append(titlePlaylist[int(old_position1) - 1])
                    queuePlaylist.pop(int(old_position1) - 1)
                    titlePlaylist.pop(int(old_position1) - 1)
                    i += 1
                i = int(new_position1)
                while (i <= int(new_position2)):
                    queuePlaylist.insert(i - 1, songLinks[0])
                    titlePlaylist.insert(i - 1, songTitles[0])
                    songLinks.pop(0)
                    songTitles.pop(0)
                    i += 1 
                await interaction.followup.send("Songs at positions " + old_position1 + " to " + old_position2
                                                + " have been moved to " + new_position1 + " to " + new_position2 + ".")
    else: # Single position
        if (not old_position.isdigit() or not new_position.isdigit()):
            await interaction.followup.send("Positions must be numbers!")
        elif (int(old_position) <= 1 or int(old_position) > len(queuePlaylist)):
            await interaction.followup.send("Cannot move song at position " + old_position)
        elif (int(new_position) <= 1 or int(new_position) > len(queuePlaylist)):
            await interaction.followup.send("Cannot move song to position " + new_position)
        elif (int(old_position) == int(new_position)):
            await interaction.followup.send("That song is already in that position idiot!")
        else:
            songLink = queuePlaylist[int(old_position) - 1]
            songTitle = titlePlaylist[int(old_position) - 1]
            queuePlaylist.pop(int(old_position) - 1)
            titlePlaylist.pop(int(old_position) - 1)
            queuePlaylist.insert(int(new_position) - 1, songLink)
            titlePlaylist.insert(int(new_position) - 1, songTitle)
            await interaction.followup.send("Song at position " + old_position + " has been moved to " + new_position + ".") 

# Randomly shuffle the current queue
@tree.command(name = "shuffle", description = "Randomly shuffle the current queue", guild = discord.Object(id=536041241972834304))
async def shuffle(interaction):
    await interaction.response.defer(ephemeral=False)
    global titlePlaylist, queuePlaylist
    currentSong = titlePlaylist[0]                                          # Keep current song in 1st position
    currentLink = queuePlaylist[0]
    queuePlaylist.pop(0)                                                    # Pop first song
    titlePlaylist.pop(0)
    temp = list(zip(queuePlaylist, titlePlaylist))
    random.shuffle(temp)                                                    # Shuffle the playlists
    queuePlaylist, titlePlaylist = zip(*temp)                               # Unpack the playlists
    queuePlaylist, titlePlaylist = list(queuePlaylist), list(titlePlaylist) # Convert back to lists
    queuePlaylist.insert(0, currentLink)                                    # Insert current playing song
    titlePlaylist.insert(0, currentSong)
    await interaction.followup.send("Shuffled the queue.")

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
        masked_link_embed = discord.Embed(
            title = titlePlaylist[0],
            description = str(queuePlaylist[0]),
        )
        await interaction.followup.send(embed=masked_link_embed)

# Clear the whole queue
@tree.command(name = "clear", description = "Clears the current queue", guild = discord.Object(id=536041241972834304))
async def clear(interaction):
    await interaction.response.defer(ephemeral=False)
    if (len(queuePlaylist) == 0):           # There is no queue to clear
        await interaction.followup.send("Silly human! There is already no queue!")
    else:                                   # There is a queue
        currentSong = titlePlaylist[0]
        currentLink = queuePlaylist[0]
        clearQueue()
        queuePlaylist.append(currentLink)   # Add back the current song (queue position 1)
        titlePlaylist.append(currentSong)
        await interaction.followup.send(f"Queue was cleared by {interaction.user.mention}")

# The viking funeral for a user
@tree.command(name = "viking_funeral", description = "Send a member a proper fairwell", guild=discord.Object(id=536041241972834304)) 
async def vikingFuneral(interaction, member : discord.Member):
    await interaction.response.defer(ephemeral=False)
    await interaction.followup.send("Fairwell " + member.mention + ". You will be missed.")
    await play_audio("https://www.youtube.com/watch?v=ofm0FXIAq1U", interaction)
    #wait for song to finish
    await asyncio.sleep(156)
    await member.kick()

# Search for a song on youtube
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

# Pick a song after searching
@tree.command(name = 'pick', description = "Pick video from search list", guild=discord.Object(id=536041241972834304))
async def pick(interaction, pick : str):
    await play_audio(interaction, f'https://www.youtube.com/watch?v={pick}', False)

# Disconnect bot from voice channel
@tree.command(name = 'disconnect', description = "Kick V.H.O.S from their current channel", guild=discord.Object(id=536041241972834304))
async def disconnect(interaction):
    await interaction.response.defer(ephemeral=False)
    voice = discord.utils.get(client.voice_clients, guild=interaction.guild)
    if voice.is_connected():     # Bot is in voice channel
        await interaction.followup.send(f"Disconnected by {interaction.user.mention}")
        clearQueue()             # Clear the queue
        await voice.disconnect() # Disconnect the bot
    else:                        # Bot is no in voice channel
        await interaction.followup.send("Dumb human, I'm not in a voice channel! (But I'll let you off the hook this time)")

@tree.command(name="kill", description="Kill V.H.O.S", guild=discord.Object(id=536041241972834304))
async def kill():
    exit()
# @tree.command(name = 'restart', description = "Restart V.H.O.S if it is stuck.", guild=discord.Object(id=536041241972834304))
# async def restart(ctx):
#     await ctx.send("Restarting bot...")
#     os.execv(sys.executable, ['python'] + sys.argv)
        
# <----- End of Commands ------>

# Update whenever there is a new reaction to a message
@client.event
async def on_reaction_add(reaction, message):
    global pageLength
    global pageNum
    global pages
    if (reaction.emoji == "\U000025B6" and reaction.count > 1):   # Resume
        await resume_audio(message)
        msg = await reaction.message.channel.send("Music resumed through reaction.")
        await msg.add_reaction("\U000023F8")                      # Pause button reaction
    elif (reaction.emoji == "\U000023F8" and reaction.count > 1): # Pause
        await pause_audio(message)
        msg = await reaction.message.channel.send("Music paused through reaction.")
        await msg.add_reaction("\U000025B6")                      # Resume button reaction
    elif(reaction.emoji == "\U00002B06" and reaction.count > 1):  # Increase queueLength
        pageLength += 5
        await reaction.message.channel.send("Increased queue length by 5.")
    elif(reaction.emoji == "\U00002B07" and reaction.count > 1):  # Decrease queueLength
        pageLength -= 5
        await reaction.message.channel.send("Decreased queue length by 5.")
    elif(reaction.emoji == "\U000023E9" and reaction.count > 1):  # Next queue page
        pageNum += 1
        view = await get_queue(pageNum)
        msg = await reaction.message.channel.send(view)
        if (pageNum == 1):
            await msg.add_reaction("\U000023E9")           # Right arrow to go to next page
        elif (pageNum == pages):
            await msg.add_reaction("\U000023EA")           # Left arrow to go to previous page
        else:
            await msg.add_reaction("\U000023EA")           # Left arrow to go to next page
            await msg.add_reaction("\U000023E9")           # Right arrow to go to previous page
        await msg.add_reaction("\U00002B06")               # Up arrow to increase queueLength
        await msg.add_reaction("\U00002B07")               # Down arrow to decrease queueLength
    elif(reaction.emoji == "\U000023EA" and reaction.count > 1):  # Previous queue page
        pageNum -= 1
        view = await get_queue(pageNum)
        msg = await reaction.message.channel.send(view)
        if (pageNum == 1):
            await msg.add_reaction("\U000023E9")           # Right arrow to go to next page
        elif (pageNum == pages):
            await msg.add_reaction("\U000023EA")           # Left arrow to go to previous page
        else:
            await msg.add_reaction("\U000023EA")           # Left arrow to go to next page
            await msg.add_reaction("\U000023E9")           # Right arrow to go to previous page
        await msg.add_reaction("\U00002B06")               # Up arrow to increase queueLength
        await msg.add_reaction("\U00002B07")               # Down arrow to decrease queueLength

# Wait and disconnect the bot after MINUTES_INACTIVE minutes
@client.event
async def on_voice_state_update(self, before, interaction):
    MINUTES_INACTIVE = 5                                 # The amount of minutes it takes for the bot to disconnect after inactivity
    if before.channel is None:
        voice = interaction.channel.guild.voice_client
        time = 0
        while True:
            await asyncio.sleep(1)                      # Wait one second
            time += 1
            if voice.is_playing() or voice.is_paused(): # If the bot is playing or paused
                time = 0
            if time == MINUTES_INACTIVE * 60:           # If the amount of minutes is reached (in seconds)
                await voice.disconnect()                # Disconnect the bot
            if not voice.is_connected():
                break

async def send_message(message, user_message, is_private):
    try:
        response = responses.handle_response(user_message)
        await message.author.send(response) if is_private else await message.channel.send(response)
    except Exception as e:
        print(e)

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

async def get_queue(page):
    global pages
    pages = math.ceil(len(queuePlaylist) / pageLength) # How many pages are needed to display the whole queue depending on what the page length is
    if page > pages:                                   # Cannot have a page selection greater than the total pages
        page = pages
    global pageNum
    pageNum = page
    view = "**Current queue (Page " + str(page) + " of " + str(pages) + "):**\n"
    queuePos = 1 + ((int(page) - 1) * pageLength)
    for i in range(queuePos, queuePos + pageLength):   # Loop through playlist and add them to view
        if (int(queuePos) - 1) < (int(page) * pageLength):
            if (int(i) <= len(queuePlaylist)):
                if queuePos == 1:                      # Currently playing
                    view += "Playing: " + titlePlaylist[i-1] + "\n"
                else:
                    view += str(queuePos) + ": " +  titlePlaylist[i-1] + "\n"
                queuePos += 1
    view += "\n**Queue length: **" + str(len(queuePlaylist)) + " - **Page length: **" + str(pageLength)
    return view

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
        voice.play(source, after=audioDone) # Play the song
        voice.is_playing()                  # Song is playing
    except Exception as e:
        print(e)

# Add title to titlePlaylist
def addTitle(link : str):                            
    if ("&list=" in link or "?list=" in link): # Inserted url is a youtube playlist 
        playlist = Playlist(link)
        for url in playlist:
            titlePlaylist.append(get_youtube_title(url))
    else:                                      # Not a youtube playlist
        titlePlaylist.append(get_youtube_title(link))
    
# Clear the queue
def clearQueue():
    titlePlaylist.clear()
    queuePlaylist.clear()

# Used in play(after=) to determine when audio is finished
def audioDone(error):
    try:
        global source
        source.cleanup()           # Cleanup the source to skip properly
        queuePlaylist.pop(0)       # Remove 0th item from link queue
        titlePlaylist.pop(0)
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