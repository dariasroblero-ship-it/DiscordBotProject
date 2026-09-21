import discord
from discord.ext import commands
import requests


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

lt_irl = 'http://localhost:5000/translate'

@bot.event
async def on_ready():
    print(f'Translation bot is ready as {bot.user}')

@bot.command()
async def translate(ctx, target_lang: str, *, text: str):
    """Usage: !translate es Hello World (translates 'Hello World' to Spanish)"""

    # Prepare data for LibreTranslate API
    payload = {
        "q": text,
        "source": "auto", # Automatically detect the input language
        "target": target_lang,
        "format": "text",
    }

    try:
        # Make the HTTP POST request to LibreTranslate
        response = requests.post(lt_irl, data=payload)
        response_data = response.json()

        if "translatedText" in response_data:
            translated_text = response_data["translatedText"]
            await ctx.send(f"**Translation ({target_lang}):** {translated_text}")
        else:
            await ctx.send(f"Translation error: {response_data.get('error', 'Unknown error')}")

    except Exception as e:
        await ctx.send(f"Failed to connect to LibreTranslate: {str(e)}")

bot.run('Discord bot token')