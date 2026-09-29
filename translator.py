import discord
from discord.ext import commands
import aiohttp
import requests

intents = discord.Intents.default() # Enables default set of Gateway Intents(recieving server events)
intents.message_content = True # Enables the bot to read text inside user messages
bot = commands.Bot(command_prefix="!", intents=intents) # Configures the "!" prefix as well as using intent
client = discord.Client(intents=intents) # Instantiates low-level discord.Client using same intents

# Initializes an empty dictionary as an in-memory database to 
# store and track active translation settings for each channel
channel_languages = {}

transl_url = 'http://localhost:5000/translate' # Translate Text

lang_url = 'http://localhost:5000/languages' # Get supported languages

detect_url = 'http://localhost:5000/detect' # Detect language of text

# Triggers a visual confirm. that the bot is online
@bot.event
async def on_ready():
    print(f'Translation bot is ready as {bot.user}')

# Translates the input using "Code"
@bot.command()

# Defines an asynchronous function called language. Ctx is a context object 
# that contains information of where the command was called. target_lang 
# captures the word typed as a string, which represents the language code.
# The * tells discord to collect all remaining words after target_lang into 
# a single string variable 
async def translate(ctx, target_lang: str, *, text: str):

    # Prepare data for LibreTranslate API
    payload = {
        "q": text, # Accepts a single string
        "source": "auto", # Auto detects the input
        "target": target_lang, # Targets the language the user wants to use
        "format": "text", # Formatted in text
    }

    try:
        # Make the HTTP POST request to LibreTranslate
        response = requests.post(transl_url, data=payload)

        # Parses the response into a Python dictionary
        response_data = response.json() 

        # If "translateText" exists in the response, it extracts the string and
        # the translated string sends the formatted message back to the chat 
        if "translatedText" in response_data:
            translated_text = response_data["translatedText"]
            await ctx.send(f"**Translation ({target_lang}):** {translated_text}")
        else:
            # Sends an error message to the chat
            await ctx.send(f"Translation error: {response_data.get('error', 'Unknown error')}")

    # Failed to connect to Libretranslate
    except Exception as e:
        await ctx.send(f"Failed to connect to LibreTranslate: {str(e)}")

# Find the "Code" of a language
@bot.command()
async def language(ctx, *, name: str):

    try:
        # Make the HTTP GET request to LibreTranslate
        response = requests.get(lang_url)

        # Parses the response into a Python dictionary
        language_data = response.json()

        # The API returns a list of languages
        if isinstance(language_data, list):

            # Initializes the language's "Code" and sets the name to an empty string 
            found_code = None
            matched_name = ""

            # Loops over each language entry and gets the "name" from the 
            # dictionary, converting it to lowercase, and checks if it matches
            # the user's input
            for lang in language_data:
                if lang.get("name","").lower() == name.lower():

                    # If match is found, stores the language name and corresponding
                    # language code 
                    matched_name = lang.get("name")
                    found_code = lang.get("code")

                    # Stops the loop when the match is found
                    break

            # If the matching language was found, it sends a message with the
            # language name and language code to discord
            if found_code:
                await ctx.send(f"**Name:** {matched_name}\n**Abbreviation Code:** `{found_code}`")
            else:

                # Sends an error message when the language name was not found
                await ctx.send(f"Language **{name}**, not found. The language selected does not exist in the current database / the selected langauge is misspelled")
        else:

            # Sends an error message that "language_data" was not a list
            await ctx.send("Error: Received unexpected data format from the translation server.")

    # Failed to connect to Libretranslate        
    except Exception as e:
        await ctx.send(f"Failed to connect to LibreTranslate: {str(e)}")

# Give instructions on how to use the bot (uses /, instead of !)
@bot.tree.command(name="instructions", description="Instructions for TranslatorBot")

# Defines a function taking an interaction function object
async def instructions(interaction: discord.Interaction):

    # Instantiates a formatted Discord Embed card 
    embed = discord.Embed(
        title="How-To instructions",
        description="Commands available for TranslatorBot"
    )

    # Adds 4 seperate sections to the embed card explaining the commands available
    embed.add_field(name="**Command 1 - !language**", value="Find the {code} for a specific language.\n\n *Example:\n (!language Spanish) = es*", inline=True)
    embed.add_field(name="**Command 2 - !translator**", value="Translate your input using a language {code}.\n\n *Example:\n (!translator es Hello) = Hola*", inline=True)
    embed.add_field(name="**Command 3 - /instructions**", value="View the instructions of TranslatorBot.\n\n *Example:\n (/instructions) = View Available Commands*", inline=True)
    embed.add_field(name="\n**Command 4 - !createroom**", value="Create a room between 2 langauge using {code}.\n\n *Example:\n (!createroom English-To-Spanish en es) = Creates a room called **English-To-Spanish** with english and spanish only being tranlated*", inline=True)

    # Responds to the / command with the created Embed. It also makes the response 
    # visible to only user who ran the command with "ephemeral=True"
    await interaction.response.send_message(embed=embed, ephemeral=True)


# Trigger the bot automatically when a new message is posted in any 
# channel the bot can see
@bot.event

# Runs automatically whenever a message is posted in any channel the bot can see
async def on_message(message):
    # Ignore messages sent by the bot itself
    if message.author == bot.user:
        return

    # Allows regular commands to still work
    await bot.process_commands(message)

    # Ignore empty messages or messages that start with the command prefix '!'
    if not message.content.strip() or message.content.startswith('!'):
        return

    # Captures the unique ID of the channel where the message was posted
    channel_id = message.channel.id

    # Checks if the auto-translator is enabled for a specific channel by
    # verifying its ID. If not, it stops
    if channel_id not in channel_languages or not channel_languages[channel_id]:
        return

    try:
        # Tries to handle asynchronous HTTP requests and server connection
        async with aiohttp.ClientSession() as session:

            # Sends an HTTP POST request containing message text to detection endpoint
            async with session.post(detect_url, json={"q": message.content}) as detect_resp:

                # If the server responds with 200, It parses the JSON response
                # to extract the detected language code. If fails, it exits the function
                if detect_resp.status == 200:
                    detect_data = await detect_resp.json()

                    if isinstance(detect_data, list) and len(detect_data) > 0:
                            current_lang = detect_data[0].get("language")
                    else:
                            current_lang = None
                else:
                    return

            # Verifies if the detected language is one of the allowed
            # languages for a specific channel. If not, the bot ignores it
            if current_lang not in channel_languages[channel_id]:
                print(f"Ignored foreign languages {current_lang}")
                return

            # It goes through all target languages configured for the channel.
            # If a target language matches the sender's current language,
            # it avoids translating the text into the language it was
            # already typed in.
            for target_lang in channel_languages[channel_id]:
                if target_lang == current_lang:
                    continue

                # Prepare data for Libretranslate API
                payload = {
                    "q": message.content, # Extracts the text sent by the user in Discord
                    "source": current_lang, # Targets the inputed message
                    "target": target_lang, # Targets the targeted language placed in the channel
                    "format": "text" # Formatted in text
                }

                # Sends an HTTP POST request to the translation endpoint
                async with session.post(transl_url, json=payload) as trans_resp:

                    # If the API succeeds, it extracts the translated string from the 
                    # returned JSON response
                    if trans_resp.status == 200:
                        trans_data = await trans_resp.json()
                        translated_text = trans_data.get("translatedText")

                        # Replies directly to the original message with the translated text 
                        # tagged with the language code
                        await message.reply(
                            f"**[{target_lang.upper()}]** {translated_text}",
                            mention_author=False # Doesn't ping the sender
                        )
    
    # Catches errors during the detection process
    except Exception as e:
        print(f"Translation system error: {e}")

# Creates a text channel locked to a 2-language translation pairing
@bot.command()
async def createroom(ctx, room_name: str, lang1: str, lang2: str):

    # Stores the Discord server where the command was called
    guild = ctx.guild
    
    # Converts both language "code" to lowercase to ensure consistency
    l1 = lang1.lower()
    l2 = lang2.lower()

    try:
        # Create a new text channel in the server using a provided name
        # and setting up a channel topic description to display the 
        # active target languages
        new_channel = await guild.create_text_channel(
            name=room_name,
            topic=f"Auto-translator room: Translation between {l1.upper()} and {l2.upper()}."
        )

        # Applies a 5-second slowmode to keep it clean and easy to read
        await new_channel.edit(slowmode_delay=5)

        # Save the channel's language pairing into the bot's memory
        channel_languages[new_channel.id] = {l1, l2}

        # Send a success message in the channel where the command was run,
        # tagging the new room and confirming set languages
        await ctx.send(
            f"Successfully created room {new_channel.mention}!\n"
            f"This room is locked to translate between **{l1.upper()}** and **{l2.upper()}**."
        )

        # Send a message inside the newly created room with explainations
        await new_channel.send(
            f"**Welcome to the Translator Room!**\n"
            f"Messages in `{l1.upper()}` will translate to `{l2.upper()}`, and vice versa.\n"
            f"*Slowmode is set to 5s. Unrecognized languages will be ignored.*\n"
            f"**Use **!deleteroom** after finishing the room created**"
        )

    # Catches and reports errors when creating a new channel
    except Exception as e:
        await ctx.send(f"Failed to create the room: {e}")

# Delete channels
@bot.command()
async def deleteroom(ctx):

        # Discord channel IDs that are safe from deletion
        safe_channels = (1551621278455304295, 1552457000288260237, 1552801125260857374)

        # Checks if the command was triggered inside one of the listed safe channels.
        # If it was, it blocks exectution
        if ctx.channel.id in safe_channels:
            await ctx.send(f"Cannot delete selected channel:{ctx.channel.mention}")
        else:
            # If the channel is not protected, it permanetly deletes the text channel
            await ctx.channel.delete() 

bot.run('Insert Token')