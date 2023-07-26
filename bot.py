import discord
from discord import app_commands
from discord.ext import commands
import responses
import nacl
from search import youtube_search
from yt_dlp import YoutubeDL
import argparse
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
import random

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.message_content = True
TOKEN = 'MTEzMTU1OTU3OTQ5NTQ0ODU5Ng.GRrkOF.9XxYeknyj7SVcsQqX2AD2k-5CAIFewCzsZ9a6k'

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
bot = commands.Bot(command_prefix='+', intents=intents)


class SimpleView(discord.ui.View):
    @discord.ui.button(label="testtesttesttesttesttesttesttesttesttesttesttesttesttesttest", style=discord.ButtonStyle.secondary, custom_id="test")
    async def hello(self, interaction: discord.Interaction, button: discord.ui.Button, interaction_type: discord.InteractionType):
        await interaction.response.send_message("Hello!", ephemeral=True)

def build_button(label):
    label = label.split(' (')
    id = label[-1]
    label = label[:-2]
    
    label = ''.join(label)
    return discord.ui.Button(label=label, style=discord.ButtonStyle.secondary, custom_id=id)


@tree.command(name = "play", description = "Play music from youtube link", guild=discord.Object(id=536041241972834304)) 
async def play(interaction, link : str):
    view = SimpleView()
    await interaction.response.send_message(view=view, content="**Here's what I found**")



async def send_message(message, user_message, is_private):
    try:
        response = responses.handle_response(user_message)
        await message.author.send(response) if is_private else await message.channel.send(response)
    except Exception as e:
        print(e)

@tree.command(name = "viking_funeral", description = "Send a member a proper fairwell", guild=discord.Object(id=536041241972834304)) 
async def vikingFuneral(interaction, member : discord.Member):
    await interaction.response.send_message("Fairwell " + member.mention + ". You will be missed.")
    await play_audio(member,"https://www.youtube.com/watch?v=ofm0FXIAq1U")
    
    #await member.kick()


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
    await interaction.response.send_message(view=view, content='\n'.join(videos))
   
@tree.command(name = 'pick', description = "Pick video from search list", guild=discord.Object(id=536041241972834304))
async def pick(interaction, pick : str):
    await play_audio(interaction, f'https://www.youtube.com/watch?v={pick}', False)

@tree.command(name = 'disconnect', description = "Kick V.H.O.S from their current channel", guild=discord.Object(id=536041241972834304))
async def disconnect(interaction):
            voice = discord.utils.get(client.voice_clients, guild=interaction.guild)
            if voice.is_connected():
                await voice.disconnect()
            else:
                await interaction.channel.send("Dumb human, I'm not in a voice channel! (But I'll let you off the hook this time)")



# asnyc function to have the bot join voice channel and play audio from youtube
async def play_audio(user_message, message, send_message=True):
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
        print(URL)
        
    # check if input link is for a playlist or a single video
        #if '&list=' in user_message:


        voice = discord.utils.get(client.voice_clients, guild=message.guild)
        try:
            channel = message.author.voice.channel
        except:
            return await message.channel.send("You're not in a voice channel, dumbass!")
        if voice == None:
            await channel.connect()
            voice = discord.utils.get(client.voice_clients, guild=message.guild)
        source = discord.FFmpegPCMAudio(executable="C:/PATH_Programs/ffmpeg.exe", source="audio.mp3")
        voice.play(source)
        voice.is_playing()
        if send_message:
            await message.channel.send(responses.get_random_quip())
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
        #play youtube audio in voice channel
        if user_message.startswith('+play'):
            await play_audio(message, user_message[6:])
        

    # Remember to run your bot with your personal TOKEN

    client.run(TOKEN)