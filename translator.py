import discord
from discord.ext import commands
import aiohttp
import requests


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
client = discord.Client(intents=intents)

channel_languages = {}

transl_url = 'http://localhost:5000/translate'

lang_url = 'http://localhost:5000/languages'

detect_url = 'http://localhost:5000/detect'

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

@bot.command()
async def instructions(ctx):
    embed = discord.Embed(
        title="How-To instructions",
        description="Commands available for TranslatorBot"
    )
    embed.add_field(name="**Command 1 - !language**", value="Find the {code} for a specific language.\n\n *Example:\n (!language Spanish) = es*", inline=True)
    embed.add_field(name="**Command 2 - !translator**", value="Translate your input using a language {code}.\n\n *Example:\n (!translator es Hello) = Hola*", inline=True)
    embed.add_field(name="**Command 3 - !instructions**", value="View the instructions of TranslatorBot.\n\n *Example:\n (!instructions) = View Available Commands*", inline=True)
    embed.add_field(name="**Command 4 - !createroom**", value="Create a room between 2 langauge using {code}.\n\n *Example:\n (!createroom English-To-Spanish es en) = Creates a room called **'English-To-Spanish'** with spanish and english only available*", inline=True)

    await ctx.send(embed=embed)

@bot.command()
async def slowmode(ctx, seconds:int):
    if seconds < 0 or seconds > 10:
        await ctx.send("Please enter a delay between 0 and 10 seconds")
        return

    try:
        await ctx.channel.edit(slowmode_delay=seconds)

        if seconds == 0:
            await ctx.send("**Slowmode has been disabled.**")
        else: 
            await ctx.send(f"**Slowmode is enabled for {seconds} seconds.**")

    except discord.Permissions:
        await ctx.send("**I do not have permission in this channel**")
    except Exception as e:
        await ctx.send(f"**An error occurred: {e}")

@bot.event
async def on_message(message):
    # Ignore messages sent by the bot itself
    if message.author == bot.user:
        return

    # CRITICAL STEP: This line allows your regular "!" commands to still work!
    # Without this, the background translator will block your commands.
    await bot.process_commands(message)

    # Ignore empty messages or messages that start with the command prefix '!'
    if not message.content.strip() or message.content.startswith('!'):
        return

    channel_id = message.channel.id

    if channel_id not in channel_languages or not channel_languages[channel_id]:
        return

    try:
        async with aiohttp.ClientSession() as session:
            # Detect language
            async with session.post(detect_url, json={"q": message.content}) as detect_resp:
                if detect_resp.status == 200:
                    detect_data = await detect_resp.json()

                    if isinstance(detect_data, list) and len(detect_data) > 0:
                            current_lang = detect_data[0].get("language")
                    else:
                            current_lang = None
                else:
                    return

            # CRITICAL CHECK: Only continue if the detected language is one of the room's chosen languages
            if current_lang not in channel_languages[channel_id]:
                print(f"Ignored foreign languages {current_lang}")
                return


            # Translate for other active languages in the channel
            for target_lang in channel_languages[channel_id]:
                if target_lang == current_lang:
                    continue

                payload = {
                    "q": message.content,
                    "source": current_lang,
                    "target": target_lang,
                    "format": "text"
                }

                async with session.post(transl_url, json=payload) as trans_resp:
                    if trans_resp.status == 200:
                        trans_data = await trans_resp.json()
                        translated_text = trans_data.get("translatedText")
                        
                        await message.reply(
                            f"**[{target_lang.upper()}]** {translated_text}",
                            mention_author=False
                        )
    except Exception as e:
        print(f"Translation system error: {e}")


@bot.command()
async def createroom(ctx, room_name: str, lang1: str, lang2: str):
    """Creates a new text channel locked to a strict 2-language translation pairing."""
    guild = ctx.guild
    
    # 1. Clean up and format the languages input
    l1 = lang1.lower()
    l2 = lang2.lower()

    try:
        # 2. Create the brand-new text channel in the server
        # We can also add a topic description so users know what it's for
        new_channel = await guild.create_text_channel(
            name=room_name,
            topic=f"Auto-translator room: Exclusive translation between {l1.upper()} and {l2.upper()}."
        )

        # 3. Optional: Automatically apply a 5-second slowmode to keep it clean
        await new_channel.edit(slowmode_delay=5)

        # 4. Save the channel's language pairing into the bot's memory
        channel_languages[new_channel.id] = {l1, l2}

        # 5. Send a success message in the current channel, tagging the new room
        await ctx.send(
            f"Successfully created room {new_channel.mention}!\n"
            f"This room is locked to translate between **{l1.upper()}** and **{l2.upper()}**."
        )

        # 6. Send a welcoming anchor message inside the newly created room
        await new_channel.send(
            f"**Welcome to the Translator Room!**\n"
            f"Messages in **{l1.upper()}** will translate to **{l2.upper()}**, and vice versa.\n"
            f"*Note: Slowmode is set to 5s. Unrecognized languages will be ignored.*"
        )

    except discord.Forbidden:
        await ctx.send("I don't have the **Manage Channels** permission to create a new room.")
    except Exception as e:
        await ctx.send(f"Failed to create the room: {e}")

@bot.command()
async def deleteroom(ctx):
        safe_channels = (1551621278455304295, 1552457000288260237, 1552801125260857374)

        if ctx.channel.id in safe_channels:
            await ctx.send(f"Cannot delete selected channel:{ctx.channel.mention}")
        else:
            await ctx.channel.delete()

bot.run('Enter Discord API token here')