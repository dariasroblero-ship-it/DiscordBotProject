import discord
from discord.ext import commands
import requests



intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

transl_url = 'http://localhost:5000/translate'

lang_url = 'http://localhost:5000/languages'

@bot.event
async def on_ready():
    print(f'Translation bot is ready as {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

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

class Instructions(discord.ui.Modal, title="Instruction for Translator Bot"):
    instructions_display = discord.ui.TextInput(
        label = "How to use this bot",
        default = "To translate into another language, use: !translate {Code} {Inputed Text} \nTo find the code for the language, use: !language {Language Name}",
        style = discord.TextStyle.paragraph,
        required=False,
        max_length=400
    )
        # You must include this method so the bot acknowledges when they close/submit the modal
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer() 

@bot.tree.command(name="instructions", description="Shows the instructions")
async def instructions(interaction: discord.Interaction):
    await interaction.response.send_modal(Instructions())

bot.run('Enter Discord Bot API')