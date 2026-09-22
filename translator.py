import discord
from discord.ext import commands
import requests
import json
from typing import Any, Dict
from urllib import request, parse
from libretranslatepy import LibreTranslateAPI

lt = LibreTranslateAPI("https://libretranslate.com/languages")


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

lt_irl = 'http://localhost:5000/translate'

la_url = 'http://localhost:5000/languages'

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

@bot.command()
async def languages(ctx, name, code):
        """Retrieve list of supported languages.

        Returns:
            A list of available languages ex: [{"code":"en", "name":"English"}]
        """

        url = la_url
        params = dict()
        # if self.api_key is not None:
        #     params["api_key"] = self.api_key
        # url_params = parse.urlencode(params)
        # req = request.Request(url, data=url_params.encode(), method="GET")
        # response = request.urlopen(req)
        # response_str = response.read().decode()
        # return json.loads(response_str)
        payload = {
            "name": name,
            "code": code
        }

        try:
            # Make the HTTP POST request to LibreTranslate
            languages = requests.get(lt, data=payload)

        
            # if "translatedText" in response_data:
            # translated_text = response_data["translatedText"]
            for code in languages.json():
                ctx.send(f"Name: {name}   Abbreviation:{code}")
            # else:
            # await ctx.send(f"Translation error: {response_data.get('error', 'Unknown error')}")
        
        except Exception as e:
            await ctx.send(f"Failed to connect to LibreTranslate: {str(e)}")

        # await ctx.send(f"{lt.languages}{lt['name']},{lt['code']}")
        

bot.run('Discord Token')