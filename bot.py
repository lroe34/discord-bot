import discord
import responses
import nacl
from yt_dlp import YoutubeDL
import os
intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.message_content = True
TOKEN = 'MTEzMTU1OTU3OTQ5NTQ0ODU5Ng.GRrkOF.9XxYeknyj7SVcsQqX2AD2k-5CAIFewCzsZ9a6k'
client = discord.Client(intents=intents)

async def send_message(message, user_message, is_private):
    try:
        response = responses.handle_response(user_message)
        await message.author.send(response) if is_private else await message.channel.send(response)
    except Exception as e:
        print(e)

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
        ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn'}
        ydl = YoutubeDL(ydl_opts)
        info = ydl.extract_info(user_message, download=True, process=True, ie_key='Youtube')
        URL = info['formats'][0]['url']
        print(URL)
        voice = discord.utils.get(client.voice_clients, guild=message.guild)
        channel = message.author.voice.channel
        if voice == None:
            await channel.connect()
            voice = discord.utils.get(client.voice_clients, guild=message.guild)
        source = discord.FFmpegPCMAudio(executable="C:/PATH_Programs/ffmpeg.exe", source="audio.mp3")
        voice.play(source)
        voice.is_playing()
        await message.channel.send('Bot is playing')
    except Exception as e:
        print(e)

def run_discord_bot():

    @client.event
    async def on_ready():
        print(f'{client.user} is now running!')

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
        if user_message.startswith('!play'):
            await play_audio(message, user_message[6:])

    # Remember to run your bot with your personal TOKEN
    client.run(TOKEN)