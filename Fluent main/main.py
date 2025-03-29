import shelve
from difflib import get_close_matches as gcm
from os import getenv
from time import strftime

import discord
from discord import Color, app_commands
from discord.ext import commands
from langcodes import Language

from iso_639_2 import iso_639_choices
from translateMOD import translate

TOKEN = '[Token]'

name = 'Fluent'

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

langs = [lang[0] for lang in iso_639_choices]

langs_dict = {lang[1]: lang[0] for lang in iso_639_choices}


@bot.event
async def on_ready():
    print('Syncing Commands...')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(e)
    print(name, 'is up and ready')
    with open('log.txt', 'a') as log:
        log.write(f'Connected at {strftime("%m/%d %H:%M:%S")}\n')

@bot.event
async def on_disconnect():
    with open('log.txt', 'a') as log:
        log.write(f'Disconnected at {strftime("%m/%d %H:%M:%S")}\n')


@bot.event
async def on_guild_join(guild):
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            embed = discord.Embed(
                title="Hello, I'm Fluent",
                color=discord.Color.default()
            )
            embed.add_field(name='', value="For a list of commands, use `/help`.", inline=False)
            embed.add_field(name='', value='For news on Bot outages and downtimes, [Follow this Announcement Channel](https://discord.gg/ycj662zxvH).')
            embed.add_field(name='', value='Or just [join the Server!](https://discord.gg/5c4EPTWEDn)')
            embed.set_footer(text='If messages are not being translated, please make sure I have the correct permissions to send messages.')
            await channel.send(embed=embed)
            break


conversation_log = {}

@bot.event
async def on_message(message):
    USER_ID = str(message.author.id)
    ID = str(message.channel.id)

    if USER_ID == '836061934502936587' and message.content.startswith('!visual'):
        embed = discord.Embed(
            title=f'Invite {name} to your server!'
        )
        embed.set_image(url='https://i.imgur.com/SLRSb5M.jpeg')
        embed.add_field(name='',
                        value='[Add To Server](https://discord.com/oauth2/authorize?client_id=1244765820970864721&permissions=274877967360&scope=bot)',
                        inline=False
                        )
        await message.channel.send(embed=embed)

    # Auto Translate
    try:
        with shelve.open(
                'channels',
                writeback=True) as channels, shelve.open('users') as users:
            toggled = channels[ID].get('toggle_translation', False)
            languages = channels[ID].get('languages', ['en'])

            if message.author != bot.user and toggled and languages and message.content:
                msg_content = message.content
                msg_author = (message.author.display_name, message.author.name,
                              message.author.id)

                if ID not in channels:
                    channels[ID] = {}
                channel_colors = channels[ID].get('user_colors', {})
                channels[ID]['user_colors'] = channel_colors

                colors = [Color.default(), Color.teal(), Color.dark_teal(), Color.green(), Color.dark_green(), 
                      Color.blue(), Color.dark_blue(), Color.purple(), Color.dark_purple(), 
                      Color.magenta(), Color.dark_magenta(), Color.gold(), Color.dark_gold(), 
                      Color.orange(), Color.dark_orange(), Color.red(), Color.dark_red(), 
                      Color.greyple(), Color.dark_grey(), Color.light_grey(), Color.blurple(), 
                      Color.light_gray()]
                color_instances = [
                    list(channel_colors.values()).count(i) for i in colors
                ]

                if msg_author[2] not in channel_colors:
                    channel_color_index = color_instances.index(
                        min(color_instances))
                    channel_colors[msg_author[2]] = colors[channel_color_index]

                
                await message.delete()
                loading_msg = await message.channel.send(
                    f'Translating "{msg_content}"'
                    f' from {msg_author[0]}...')
                embed = discord.Embed(
                    title=f'{msg_author[0]} (@{msg_author[1]})',
                    color=channel_colors[msg_author[2]])

                if message.attachments:
                    for attachment in message.attachments:
                        embed.add_field(name='',
                                        value=attachment.url,
                                        inline=True)

                embed.add_field(name="Message",
                                value=f"{msg_content}",
                                inline=False)

                for lang in sorted(languages):
                    translation = translate(msg_content, lang)
                    if translation.lower() != msg_content.lower():
                        embed.add_field(
                            name=Language.make(language=lang).display_name(),
                            value=translation,
                            inline=False)
                await loading_msg.delete()
                await message.channel.send(embed=embed)
    except Exception:
        pass


# Toggle auto-translation
@bot.tree.command(name='auto_translate',
                  description='Toggle auto-translation in channel')
async def toggle_translation(interaction: discord.Interaction):
    ID = str(interaction.channel.id)

    with shelve.open('channels', writeback=True) as channels:
        try:
            channels[ID][
                'toggle_translation'] = not channels[ID]['toggle_translation']
        except KeyError:
            channels[ID] = {'toggle_translation': False}
            channels[ID][
                'toggle_translation'] = not channels[ID]['toggle_translation']
        if channels[ID]['toggle_translation']:
            await interaction.response.send_message(
                'Translation is now enabled')
        else:
            await interaction.response.send_message(
                'Translation is now disabled')


# Add Language
@bot.tree.command(name='add_lang',
                  description='Add a language to translate in channel')
@app_commands.describe(language='Language code (Example: en, ko, etc.)')
async def add_language(interaction: discord.Interaction, language: str):
    if language in langs:
        lang_name = Language.make(language).display_name()
        ID = str(interaction.channel.id)
        with shelve.open('channels', writeback=True) as channels:
            try:
                if language not in channels[ID]['languages']:
                    channels[ID]['languages'].append(language)
                else:
                    await interaction.response.send_message(
                        f'{lang_name} is already in the list', ephemeral=True)
                    return  # Return to prevent sending multiple responses
            except KeyError:
                try:
                    channels[ID]['languages'] = ['en']
                    if language not in channels[ID]['languages']:
                        channels[ID]['languages'].append(language)
                    else:
                        await interaction.response.send_message(
                            f'{lang_name} is already in the list',
                            ephemeral=True)
                        return  # Return to prevent sending multiple responses
                except Exception:
                    pass
            await interaction.response.send_message(
                f'{lang_name} added to translation')
    else:
        await interaction.response.send_message(
            f'{language} is not a valid language code', ephemeral=True)


# Remove Language
@bot.tree.command(name='remove_lang',
                  description='Remove a language from translate in channel')
@app_commands.describe(language='Language code (Example: en, ko, etc.)')
async def remove_language(interaction: discord.Interaction, language: str):
    ID = str(interaction.channel.id)
    with shelve.open('channels', writeback=True) as channels:
        try:
            if language in channels[ID]['languages']:
                channels[ID]['languages'].remove(language)
                await interaction.response.send_message(
                    f'{Language.make(language).display_name()} removed from translation'
                )
            else:
                await interaction.response.send_message(
                    f'{language} was never in to translation', ephemeral=True)
        except KeyError:
            channels[ID]['languages'] = ['en']
            if language in channels[ID]['languages']:
                channels[ID]['languages'].remove(language)
                await interaction.response.send_message(
                    f'{Language.make(language).display_name()}'
                    ' removed from translation')

# View Languages
@bot.tree.command(
    name='view_langs',
    description='View all selected languages to be translated in channel')
async def view_languages(interaction: discord.Interaction):
    ID = str(interaction.channel.id)
    with shelve.open('channels', writeback=True) as channels:
        # Ensure 'languages' key is initialized
        if 'languages' not in channels.get(ID, {}):
            channels[ID] = channels.get(ID, {})
            channels[ID]['languages'] = ['en']

        selected_langs = channels[ID]['languages']
        lang_names = [f'{Language.make(language=lang).display_name()} ({lang})' for lang in selected_langs]

        await interaction.response.send_message(
            f'Selected languages: {", ".join(lang_names)}',
            ephemeral=True)


# Translate
@bot.tree.command(name='translate', description='Translate anything')
@app_commands.describe(text='Text to translate',
                       language='Language code (Example: en, ko, etc.)')
async def translate_text(interaction: discord.Interaction, text: str,
                         language: str):
    lang_name = Language.make(language).display_name()
    if language in langs:
        await interaction.response.send_message(translate(text, language),
                                                ephemeral=True)


# Search Language Code
@bot.tree.command(name='search_langcode', description='Search for a Language Code based on English name for Language')
@app_commands.describe(language='Language name in English (Example: English, Korean, etc.)')
async def search_lang(interaction: discord.Interaction, language: str):
    prob_lang = gcm(language, langs_dict.keys(), 1, 0.6)
    if prob_lang:
        await interaction.response.send_message(f'{prob_lang[0]}: {langs_dict[prob_lang[0]]}', ephemeral=True)
    else:
        await interaction.response.send_message('Sorry, I could not find a language with that name', ephemeral=True)


# Help Command
@bot.tree.command(name='help', description='List all available commands')
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Available Commands",
        color=discord.Color.default()
    )
    embed.add_field(name="/auto_translate", value="Toggle auto-translation in channel", inline=False)
    embed.add_field(name="/add_lang", value="Add a language to translate in channel", inline=False)
    embed.add_field(name="/remove_lang", value="Remove a language from translation in channel", inline=False)
    embed.add_field(name="/view_langs", value="View all selected languages to be translated in channel", inline=False)
    embed.add_field(name="/translate", value="Translate anything", inline=False)
    embed.add_field(name="/search_langcode", value="Search for a Language code using the English name for the language", inline=False)
    embed.set_footer(text="Use the command names with a slash (/) at the beginning.")

    await interaction.response.send_message(embed=embed, ephemeral=True)

bot.run(TOKEN)
