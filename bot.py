# bot.py
import os
import asyncio
import random
import json
import time
from enum import Enum
from pathlib import Path
from win10toast import ToastNotifier
from dotenv import load_dotenv

import discord
from discord.ext import commands

#TODO
#//these two are actually not needed, it works perfectly fine as it is and would just make it less performant, the only advantage would be the possibility of blank lines, which is actually not necessary atm I think)
#(use , as seperator for phrases and answers)
#(correct comma recognition)  
#//I find it rather spammy, so I probably won't implement it, but Caro insisted I put it on here, so I'll just keep it and might delete it sometime else
#(DM new users) 
#
#!wiki command
#I'm ... Dadjoke
#text adventure     //programming-wise pretty boring but really cool mechanic
#reload DM chats (get messages written in absence and old ones) (command usable in DM by Admin only?) (on Bot start?)

#Constants
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents = intents)

toast = ToastNotifier()

#Files used:
COUNTER_FILE = 'counter.json'
PHRASE_FILE = 'Phrases.data'

###############################
# Phrase Data file Formatting #
###############################

#Start and end a section with opening and closing tags f.e. [example] <- open [/example] <- close, while the opening tag is optional (but encouraged), the closing one is mandatory
#follow up with phrases= "phrase1" <- please be sure to write phrases= without spaces, phrases can only be lowercase only and enclosed by double quotes
#if multiple phrases should be considered, put one phrase per line, each one enclosed in its own set of double quotes and put a comma (,) after every line except for the last one
#follow up with answers= "answer1" <- consider the same style guides as for phrases
#for phrases= and answers= the phrases and answers can be indented to increase human readability/maintainability
#follow up with everybody= True or everybody= False while true can effectively be anything that doesn't start with False, False will be checked and case sensitive
#optionally follow up with special=, any special effects have to be programmed by hand, the file can merely contain identifiers
#between opening and closing tags there must not be any blank lines, or lines containing things not described here, out of the tags anything not used as identifier (e.g. phrases=) can be used to comment

#logic variables
if os.path.isfile(COUNTER_FILE):
    with open(COUNTER_FILE) as handle:
        good_bot_counter = json.load(handle)
else:
    good_bot_counter = 0


#these are to be used asynchronously, so that the rest of the program can continue
async def wait_and_unmute(user, role, t):
    await asyncio.sleep(t)
    await user.remove_roles(role)

#this list will save the messages containing forbidden emojis, so that the corresponding authors can be assigned roles on the correct servers
emoji_muted = list()

#####################
# UTILITY FUNCTIONS #
#####################

class gameStates(Enum):
    OFF = 0
    INIT = 1
    ROUND = 2
    POSTROUND = 3

class wordchain():
    player_count = 3
    players = list()
    status = gameStates.OFF
    sentence = list()
    incrementor = 0

wordchainHandler = wordchain()

def rotate(l, n):
    return l[-n:] + l[:-n]

#def rotate(l, n):
#    return l[n:] + l[:n]

#[1,2,3,4]
#[2,3,4,1]

############
# COMMANDS #
############

@bot.command(name='wortkette', help= 'Starte oder Stoppe das Wortketten spiel (ja ich weiß dass das Scheiße klingt wenn ihr eine bessere Idee habt immer her damit!)', aliases=['Wortkette', 'wortketten', 'Wortketten', 'wordchain', 'Wordchain'])
async def wortkette(ctx, player_count: int = 3):
    global wordchainHandler
    if wordchainHandler.status == gameStates.OFF:
        wordchainHandler.status = gameStates.INIT
        wordchainHandler.player_count = player_count
        await ctx.send("Starting: ")
        await ctx.send("Every Participant should now send a message in the order you want to start")
        return
    if not wordchainHandler.status == gameStates.OFF:
        wordchainHandler.status = gameStates.OFF
        wordchainHandler.players.clear()
        wordchainHandler.sentence.clear()
        await ctx.send('Stopping...')
        return

@bot.command(name='wordchainhelp', help= 'gain information on the current state of the wordchain game')
async def wordchainhelp(ctx):
    await ctx.send(f'Game Status: {wordchainHandler.status}')
    await ctx.send(f'Player Count: {wordchainHandler.player_count}')
    await ctx.send(f'Players: {wordchainHandler.players}')
    if wordchainHandler.status == gameStates.ROUND:
        await ctx.send(f'Turn: {wordchainHandler.players[wordchainHandler.incrementor]}')

#roll a dice to get a random number between 0 and the third argument or 6 as a standard, the second argument allows you to roll multiple rolls at once
@bot.command(name='dice', help='roll a dice')
async def dice(ctx, amount_sides: int = 6, amount_dices: int = 1):
    if amount_sides <=0 or amount_dices<=0:
        await ctx.send('negative or 0 values are not allowed here!')
        return
    if amount_sides > 1000000:
        await ctx.send('please limit yourself to 1000000 sides or less, too high numbers can cause errors')
        return
    if amount_dices > 100:
        await ctx.send('please limit yourself to 100 dices or less to reduce impact on my server')
        return

    dice = [
        str(random.choice(range(1, amount_sides+1)))
        for _ in range(amount_dices)
    ]
    await ctx.send(', '.join(dice))

#get the amount of goodbots, subtracting the amounts of bad bots
@bot.command(name='goodBot', help='find out how often SuperBot was complimented yet!', aliases=['goodbot', 'good_bot'])
async def goodBot(ctx):
    await ctx.send(f'I was already complimented {good_bot_counter} times (minus the times I was reproved)')

#this one is more or less obsolete, I just created it as a learning tool, I should probably delete it, but I won't do that now
@bot.command(name='create_channel', help='create a new channel via this command')
@commands.has_role('Admin')
async def create_channel(ctx, channel_name='channel'):
    guild = ctx.guild
    existing_channel = discord.utils.get(guild.channels, name=channel_name)
    if not existing_channel:
        await ctx.send(f'creating new channel: {channel_name}')
        await guild.create_text_channel(channel_name)

#check if the bot is online, if it is, it will reply with Pong!
@bot.command(name='ping', help='check if the bot is online (and working)')
async def ping(ctx):
    await ctx.send('Pong!')

#mute orCa64 for 15 seconds or a larger amount given as argument, the unit can be given as second argument, limited between seconds and hours
@bot.command(name='CaroIstToll', help='show your affection to Caro by giving her what she deserves most, a break from talking', aliases=['caroisttoll', 'Caroisttoll'])
async def caroIstToll(ctx, t: int = 15, format = 's'):
    if 'orCa64' == ctx.message.author.name:
        await ctx.send('You left your brain in the kitchen or what?')
        t = 600
    match format:
        case 's'|'S':   #s/S for seconds
            pass        #t stays the same
        case 'm'|'M':   #m/M for minutes
            t *= 60     #t is converted to seconds
        case 'h'|'H':   #h/H for hours
            t *= 3600    #t is converted to seconds
        case _:
            await ctx.send('please give only valid format abbreviations (s, S, m, M, h, H)!')
    caro = None
    for member in ctx.guild.members:
        if member.name == 'orCa64':
            caro = member
            break
    role = discord.utils.get(ctx.guild.roles, name='muted')
    if role == None:
        await ctx.send('please create a "muted" role to apply!')
        return
    await caro.add_roles(role)
    await ctx.send(f'Caro has been muted for {t} seconds')
    asyncio.get_event_loop().create_task(wait_and_unmute(caro, role, t))

#mute a given user (or yourself if not given) for a given time period or 10 minutes as standard, the confirmation message will always give the time in seconds (as I am too lazy to program something else, maybe in the future (SUGGESTION))
@bot.command(name='mute', help='mute a member of your server')
@commands.has_role('Admin')
async def mute(ctx, target: discord.Member = None, t: int = 10, format = 'm'):
    if target == None:
        target = ctx.author
    match format:
        case 's'|'S':   #s/S for seconds
            pass        #t stays the same
        case 'm'|'M':   #m/M for minutes
            t *= 60     #t is converted to seconds
        case 'h'|'H':   #h/H for hours
            t *= 3600    #t is converted to seconds
        case _:
            await ctx.send('please give only valid format abbreviations (s, S, m, M, h, H)!')
    role = discord.utils.get(ctx.guild.roles, name = 'muted')
    if role == None:
        await ctx.send('please create a "muted" role to apply!')
        return
    await target.add_roles(role)
    await ctx.send(f'{target} was muted for {t} seconds')
    asyncio.get_event_loop().create_task(wait_and_unmute(target, role, t))

#get a codenames lobby link
@bot.command(name='codenames', help='', aliases=['Codenames'])
async def codenames(ctx):
    await ctx.send('https://codenames.game/room/delta-hotel-school')

@bot.command(name='reloadLogs', help='If you don\'t know what this does it\'s not meant for you')
async def reloadLogs(ctx):
        if ctx.message.author.name == 'Superrobs':
            for guild in bot.guilds:
                for member in guild.members:
                    Path('DMs/Reloads/').mkdir(parents=True, exist_ok=True)
                    path = 'DMs/Reloads/'+member.name+'.data'
                    with open(path, 'a+', encoding='utf-8') as f:
                        if member.dm_channel:
                            for message in member.dm_channel.history():
                                f.write(message.author.name+': '+message.content+'\n')

#catch missing permission error
#this might be considered an event but it can only be triggered by a command, thus belongs to them, so it is here and not in the Events category
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('No, you not. Not over my dead executable!')

##########
# EVENTS #
##########

#broadcast successfull connection to the console
@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

#send a welcome message
@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.channels, name='new-humans')
    await channel.send('Welcome to this Server')

#react to certain messages
@bot.event
async def on_message(message):

    #If the message is a DM, it is answered logged and can then be handled as a phrase/command
    if isinstance(message.channel, discord.channel.DMChannel):
        #get whether a person who created a DM is in the emoji_muted list
        item = None
        for item in emoji_muted:
            if item.author == message.author:
                break
        #check whether the user used the correct passphrase
        if (message.content.lower() == 'bitte entschuldige die beleidigungen') and item != None and message.author == item.author:
            #if he has, find the member instance of the user in the correct guild and remove the muted role and the entry in emoji_muted
            await message.channel.send('accepted')
            guild = item.guild
            for member in guild.members:
                if member.name == message.author.name:
                    break
            emoji_muted.remove(item)
            await member.remove_roles(discord.utils.get(item.guild.roles, name='muted'))
        #save message to {username}.data
        if not message.author.bot:
            toast.show_toast(message.channel.recipient.name,message.content,duration=20, threaded=True)
        Path('DMs/').mkdir(parents=True, exist_ok=True)
        path = 'DMs/'+message.channel.recipient.name+'.data'
        with open(path, 'a+', encoding='utf-8') as f:
            f.write(message.author.name+': '+message.content+'\n')

    #don't react to own or other bots' messages to avoid infinite self answer loops (f.e. a possible hello loop)
    if message.author.bot:
        return

    blocked_users = [
        "purplpasta"
    ]

    if message.author.name in blocked_users:
        #even if one doesn't want to be bothered by msg reactions, if he types a command that can be seen as agreement to receiving an answer
        await bot.process_commands(message)
        return
    
    #wordchain stuff
    if not isinstance(message.channel, discord.channel.DMChannel):
        if message.channel.name == 'wortketten':
            if wordchainHandler.status == gameStates.INIT:
                if not message.author.name in wordchainHandler.players:
                    wordchainHandler.players.append(message.author.name)
                    if wordchainHandler.player_count == len(wordchainHandler.players):
                        wordchainHandler.status = gameStates.ROUND
                        await bot.process_commands(message)
                        await message.channel.send('-')
                        await message.channel.send('please enter your part of the sentence now:')
                        return
            if wordchainHandler.status == gameStates.ROUND:
                if message.author.name == wordchainHandler.players[wordchainHandler.incrementor]:
                    wordchainHandler.incrementor += 1
                    wordchainHandler.sentence.append(message.content.replace('||','' ).strip())
                if len(wordchainHandler.sentence) >= wordchainHandler.player_count:
                    wordchainHandler.incrementor = 0
                    wordchainHandler.status = gameStates.POSTROUND
                    wordchainHandler.players = rotate(wordchainHandler.players, 1)
            if wordchainHandler.status == gameStates.POSTROUND:
                #content = ''
                #for part in wordchainHandler.sentence:
                #    if not content ==  '':
                #        content = content + ' '
                #    content = content + part
                #await message.channel.send(content)
                await message.channel.send('-')
                wordchainHandler.sentence.clear()
                wordchainHandler.status = gameStates.ROUND

            

        illegal_channels = [
            #Bot Testing
            'notes',
            'commands',
            #Creative Name
            'roles',
            'events',
            'dj-wünsche',
            'wortketten',
            'mc-server-log',
            'map-channel',
            'muted-hints'
        ]
    
        #don't react to messages in illegal channels
        for channel in illegal_channels:
            if channel == message.channel.name:
                await bot.process_commands(message)
                return

    #this will save a list of answers from which one will be selected to be broadcast, this one is the only one used out of the open file
    possible_answers = list()
    with open(PHRASE_FILE, 'r', encoding='utf-8') as f:
        #key will save at which part of a phrase-answer-set the program is just reading
        key = ''
        #for the addition of an extra message for specific users
        added_msg = list()
        #as it's defined out of scope it might not be cleared yet (even though it should be) I am not sure whether this is necessary (prly not) but I don't really see a reason to remove it
        possible_answers.clear()
        #this is set true if a fitting keyphrase was found to search for the corresponding answers in the following
        searchAnswers = False
        #contains the file
        data = list(f)
        for line in data:
            #if searchAnswers:
            #    print(line)
            #triggered by addMult
            if key == 'searchMult':
                start = line.index('"')
                end = line.index('"',start+1)
                added_msg.append(line[start+1:end])
                #MUST BE AT END OF LINE TO NOT CATCH COMMAS IN PHRASES
                if not (',' in line):
                    key = ''
            #if the message is found and there's an extra case for one or more users
            if key == 'False' and searchAnswers:
                if (message.author.name+':') in line:
                    start = line.index('"')
                    end = line.index('"',start+1) 
                    if 'add=' in line: 
                        added_msg.append(line[start+1:end])
                    if 'replace=' in line:
                        possible_answers.clear()
                        possible_answers.append(line[start+1:end])
                    if 'addMult=' in line:
                        start = line.index('"')
                        end = line.index('"',start+1)
                        added_msg.append(line[start+1:end])
                        #MUST BE AT END OF LINE TO NOT CATCH COMMAS IN PHRASES
                        if ',' in line:
                            key = 'searchMult'
                        else:
                            key = ''
                    if 'replaceMult=' in line:
                        possible_answers.clear()
                        start = line.index('"')
                        end = line.index('"',start+1)
                        possible_answers.append(line[start+1:end])
                        if ',' in line[end:]:
                            key = 'searchMult'
                        else:
                            key = ''
            #set key to the corresponding state
            if 'phrases=' in line:
                key = 'phrases'
            elif 'answers=' in line:
                key = 'answers'
            elif 'everybody=' in line:
                #getting from Character 11(after 'everybody= ' to 16 (entrapping a hypothetical False or a True including the \n (this would not pass checks later on)))
                key = line[11:16]
            #handle special assignments (these are handled by hand, not read from file in any way, except for an identifier)
            elif 'special=' in line and searchAnswers:
                global good_bot_counter
                if 'increment_good_bot' in line:
                    good_bot_counter += 1
                elif 'decrement_good_bot' in line:
                    if good_bot_counter > 0:
                        good_bot_counter -= 1
                with open(COUNTER_FILE, 'w') as handle:
                    json.dump(good_bot_counter, handle)
                if 'mute' in line:
                    role = discord.utils.get(message.guild.roles, name='muted')                 
                    if role == None:
                        await message.channel.send('please create a "muted" role to apply!')
                        return
                    await message.author.add_roles(role)
                    emoji_muted.append(message)
            #compare message with phrases in file to see if any matches
            if key == 'phrases':
                start = line.index('"')
                end = line.index('"',start+1)
                if line[start+1:end] in message.content.lower():   
                    searchAnswers = True
            #if searchAnswers is true and an answers section is reached, save these answers to possible_answers
            elif searchAnswers and key == 'answers':
                start = line.index('"')
                end = line.index('"',start+1)
                possible_answers.append(line[start+1:end])
            #this is part of every ending tag and thus will be used as escape combination, making the closing tag mandatory while the opening tag is not (even though greatly encouraged)
            elif searchAnswers and '[/' in line:
                break
        else:
            #before the return eventual commands have to be processed
            await bot.process_commands(message)
            return
        
        #a random of the answers saved in possible_answers is choosen and broadcast
        msg = random.choice(possible_answers)
        await message.channel.send(msg)

        #if a personalized message was added it is broadcast, too
        if added_msg:
            for msg in added_msg:
                time.sleep(2)
                await message.channel.send(msg)


    #again, handle commands before end of function
    await bot.process_commands(message)

bot.run(TOKEN)