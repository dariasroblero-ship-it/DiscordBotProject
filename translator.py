import discord
from discord.ext import commands
import requests
import json
from libretranslatepy import LibreTranslateAPI



intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

transl_url = 'http://localhost:5000/translate'

lang_url = 'http://localhost:5000/languages'

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
        response = requests.post(transl_url, data=payload)
        response_data = response.json()

        if "translatedText" in response_data:
            translated_text = response_data["translatedText"]
            await ctx.send(f"**Translation ({target_lang}):** {translated_text}")
        else:
            await ctx.send(f"Translation error: {response_data.get('error', 'Unknown error')}")

    except Exception as e:
        await ctx.send(f"Failed to connect to LibreTranslate: {str(e)}")

@bot.command()
async def language(ctx, *, name: str):
    try:
        response = requests.get(lang_url)
        language_data = response.json()

        if isinstance(language_data, list):
            found_code = None
            matched_name = ""

            for lang in language_data:
                if lang.get("name","").lower() == name.lower():
                    matched_name = lang.get("name")
                    found_code = lang.get("code")
                    break

            if found_code:
                await ctx.send(f"**Name:** {matched_name}\n**Abbreviation Code:** `{found_code}`")
            else:
                await ctx.send(f"Language **{name}**, not found. The language selected does not exist in the current database / the selected langauge is misspelled")
        else:
            await ctx.send("Error: Received unexpected data format from the translation server.")

    except Exception as e:
        await ctx.send(f"Failed to connect to LibreTranslate: {str(e)}")
        

bot.run('MTU1MTYzNjg3ODQ3Njg0NTEwNw.GI4AR_.0t9msgFTs4mSMmElnemjQHdTe8HV5Wx9MH9zxs')