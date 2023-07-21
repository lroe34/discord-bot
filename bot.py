import discord
from discord.ext import commands
import responses
import nacl
from yt_dlp import YoutubeDL
import os
import random
intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.message_content = True
TOKEN = 'MTEzMTU1OTU3OTQ5NTQ0ODU5Ng.GRrkOF.9XxYeknyj7SVcsQqX2AD2k-5CAIFewCzsZ9a6k'
client = discord.Client(intents=intents)

bot = commands.Bot(command_prefix='+', intents=intents)

async def send_message(message, user_message, is_private):
    try:
        response = responses.handle_response(user_message)
        await message.author.send(response) if is_private else await message.channel.send(response)
    except Exception as e:
        print(e)

@bot.command(name="viking funeral")
@commands.has_permissions(kick_members=True)
async def viking_funeral(ctx, member : discord.Member, *, reason=None):
    await member.kick(reason=reason)

# asnyc function to have the bot join voice channel and play audio from youtube
async def play_audio(message, user_message):
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
        await message.channel.send(responses.get_random_quip())
    except Exception as e:
        print(e)

def run_discord_bot():

    @client.event
    async def on_ready():
        print(f'{client.user} is now running!')
        await client.change_presence(activity=discord.Streaming(name='your data off-planet', url='https://www.youtube.com/watch?v=dQw4w9WgXcQ'))
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

        # If the user message contains a '?' in front of the text, it becomes a private message
        if user_message[0] == '?':
            user_message = user_message[1:]  # [1:] Removes the '?'
            await send_message(message, user_message, is_private=True)
        else:
            await send_message(message, user_message, is_private=False)
        #play youtube audio in voice channel
        if user_message.startswith('+play'):
            await play_audio(message, user_message[6:])
        

        # disconnect bot from voice channel
        if user_message.startswith('+kick'):
            voice = discord.utils.get(client.voice_clients, guild=message.guild)
            if voice.is_connected():
                await voice.disconnect()
                await message.channel.send("I'm outta here!")
            else:
                await message.channel.send("Dumb human, I'm not in a voice channel! (But I'll let you off the hook this time)")

    # Remember to run your bot with your personal TOKEN

    client.run(TOKEN)