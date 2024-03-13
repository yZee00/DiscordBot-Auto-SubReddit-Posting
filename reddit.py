import os
import discord
from discord.ext import commands
from discord.ext import tasks
from reddit_checker import check_reddit, scheduled_check
import praw
import asyncpraw
import mysql.connector
from dotenv import load_dotenv
from apscheduler.triggers.interval import IntervalTrigger
from collections import defaultdict
import re

load_dotenv()

intents = discord.Intents.all()

TOKEN = os.getenv('REDDIT')

CLIENT_ID = os.getenv('CLIENT_ID')
SECRET = os.getenv('SECRET')
AGENT = os.getenv('AGENT')

USER = os.getenv('USER')
PASS = os.getenv('PASS')
DATABASE = os.getenv('DATABASEREDDIT')

freegames = mysql.connector.connect(
    host="localhost",
    user= USER,
    password= PASS,
    database= DATABASE
)
print("freegamesDB: " + str(freegames))

freegamesDB = freegames.cursor()

# Discord bot setup
bot = commands.Bot(command_prefix='!!!', help_command=None, intents=intents)

allowed_role_ids = [CHANGE THIS HERE]

restricted_channels = [CHANGE THIS HERE]

# Store the last posted URL
last_posted_url = {}

def ensure_connection():
    try:
        # Check if connection is alive
        freegames.ping(reconnect=True, attempts=3, delay=5)
    except mysql.connector.Error as err:
        print(f"Error while reconnecting to the database: {err}")
        # Handle reconnection error if needed

@tasks.loop(hours=24)
async def scheduled_task():
    reddit = asyncpraw.Reddit(client_id=CLIENT_ID, client_secret=SECRET, user_agent=AGENT)
    channel_private = bot.get_channel(CHANGE THIS HERE)
    try:
        ensure_connection()
        await channel_private.send("Running scheduled task!")
        freegamesDB.execute("SELECT subreddit, channel_id FROM channel1")
        rows = freegamesDB.fetchall()
        for subreddit_name, discord_channel_id in rows:
            result = await check_reddit(reddit, subreddit_name, discord_channel_id)
            if result:
                channel = bot.get_channel(int(discord_channel_id))
                if channel:
                    if result.endswith('.mp4'):
                        await channel.send(file=discord.File(result))
                        os.remove(result)  # Remove the file after sending
                    else:
                        await channel.send(result)
                # Call remove_duplicates
                await auto_remove_duplicates(channel)
        await channel_private.send("Latest posts have been sent.")
    except mysql.connector.Error as err:
        print(f"Failed to fetch data from the database: {err}")
    except Exception as e:
        print(f"[ERROR] | {e}")

@bot.event
async def on_message(message):
    # Ignore messages sent by the bot itself
    if message.author == bot.user:
        return

    # Check if the message is in one of the restricted channels
    if message.channel.id in restricted_channels:
        # Check if the user has any of the allowed roles
        user_roles = [role.id for role in message.author.roles]
        if any(role in user_roles for role in allowed_role_ids):
            # User has an allowed role, do not delete the message
            pass
        else:
            # Regular expression to match Discord and Telegram invite links
            if re.search(r'(discord\.gg\/[a-zA-Z0-9]+)|(t\.me\/[a-zA-Z0-9]+)|(telegram\.me\/[a-zA-Z0-9]+)|(discord\.com\/[a-zA-Z0-9]+)', message.content):
                await message.delete()
                print(f"User {message.author} banned for posting links")
                try:
                    await message.author.ban(reason="Posting prohibited links")
                except discord.Forbidden:
                    print(f"I don't have permissions to ban {message.author.name}")
                except discord.HTTPException as e:
                    print(f"Failed to ban {message.author.name}: {str(e)}")
    
    # Process commands if any
    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    if not scheduled_task.is_running():
        scheduled_task.start()
    game_name = ""
    await bot.change_presence(activity=discord.Game(name=game_name))

@bot.event
async def on_member_join(member):
    # Replace 'your_channel_id' with the actual channel ID where you want to send the message
    channel_id = CHANGE THIS HERE
    channel = bot.get_channel(channel_id)

    if channel:
        # Sending the message to the specified channel
        await channel.send(f"**Welcome** {member.mention}! \nGet access to **ALL** channels here: <#1184938066452951122>")

    else:
        print(f"Channel with ID {channel_id} not found.")

@bot.command(name='monitor')
async def monitor(ctx, subreddit_name: str, discord_channel_id: int):
    if any(role.id in allowed_role_ids for role in ctx.author.roles):
        reddit = asyncpraw.Reddit(client_id=CLIENT_ID, client_secret=SECRET, user_agent=AGENT)
        try:
            ensure_connection()
            # Check for duplicate entries
            freegamesDB.execute("SELECT * FROM channel1 WHERE subreddit = %s AND channel_id = %s",
                                (subreddit_name, discord_channel_id))
            if freegamesDB.fetchone():
                await ctx.send("This subreddit is already being monitored in the specified channel.")
                return

            # Save to database
            freegamesDB.execute("INSERT INTO channel1 (subreddit, channel_id) VALUES (%s, %s)",
                                (subreddit_name, discord_channel_id))
            freegames.commit()
            await ctx.send("Subreddit successfully added to the monitoring list.")
        except mysql.connector.Error as err:
            print(f"Database error: {err}")
            await ctx.send("Failed to save to the database.")
            return

        # Immediate check
        url = await check_reddit(reddit, subreddit_name, discord_channel_id)
        if url:
            channel = bot.get_channel(discord_channel_id)
            if url.endswith('.mp4'):
                await channel.send(file=discord.File(url))
                os.remove(url)  # Remove the file after sending
            else:
                if channel:
                    await channel.send(url)
            # Call remove_duplicates
            await auto_remove_duplicates(channel)
    else:
        await ctx.send("You do not have permission to use this command.")
        print(f"{ctx.author.name} does not have permission to use the command.")

@bot.command(name='postlatest')
async def post_latest(ctx):
    if any(role.id in allowed_role_ids for role in ctx.author.roles):
        reddit = asyncpraw.Reddit(client_id=CLIENT_ID, client_secret=SECRET, user_agent=AGENT)
        try:
            ensure_connection()
            freegamesDB.execute("SELECT subreddit, channel_id FROM channel1")
            rows = freegamesDB.fetchall()
            for subreddit_name, discord_channel_id in rows:
                result = await check_reddit(reddit, subreddit_name, discord_channel_id)
                if result:
                    channel = bot.get_channel(int(discord_channel_id))
                    if channel:
                        if result.endswith('.mp4'):
                            await channel.send(file=discord.File(result))
                            os.remove(result)  # Remove the file after sending
                        else:
                            await channel.send(result)
                    # Call remove_duplicates
                    await auto_remove_duplicates(channel)
            await ctx.send("Latest posts have been sent.")
        except mysql.connector.Error as err:
            print(f"Failed to fetch data from the database: {err}")
        except Exception as e:
            print(f"[ERROR] | {e}")

@bot.command(name='giverole', help='Give a new role to all members with a specific role')
@commands.has_permissions(manage_roles=True)
async def give_role(ctx, current_role_name: str, new_role_name: str):
    guild = ctx.guild

    current_role = discord.utils.get(guild.roles, name=current_role_name)
    new_role = discord.utils.get(guild.roles, name=new_role_name)

    if not current_role or not new_role:
        await ctx.send("One or both specified roles do not exist.")
        return

    for member in guild.members:
        if current_role in member.roles:
            try:
                await member.add_roles(new_role)
                print(f"Added {new_role.name} to {member.name}")
            except Exception as e:
                print(f"Failed to add role to {member.name}: {str(e)}")

    await ctx.send(f"Role '{new_role.name}' has been given to all members with the '{current_role.name}' role.")


@bot.command(name='removeduplicates', help='Remove duplicate messages in a channel')
@commands.has_permissions(manage_messages=True)
async def remove_duplicates(ctx, limit: int = 10):
    if limit > 1000:  # Discord's maximum limit for fetching messages in one go
        print("Limit is too high. Please use a number less than or equal to 1000.")
        return

    try:
        messages = [msg async for msg in ctx.channel.history(limit=limit)]
    except Exception as e:
        print(f"Error fetching messages: {e}")
        return

    seen = defaultdict(list)
    duplicates = []

    for msg in messages:
        # This will group messages by their content
        seen[msg.content].append(msg)

    for msgs in seen.values():
        if len(msgs) > 1:
            duplicates.extend(msgs[1:])  # Skip the first occurrence, remove the rest

    for msg in duplicates:
        try:
            await msg.delete()
        except Exception as e:
            print(f"Failed to delete message: {e}")

    print(f"Removed {len(duplicates)} duplicate messages.")

async def auto_remove_duplicates(channel, limit=10):
    if limit > 1000:
        print("Limit is too high. Please use a number less than or equal to 1000.")
        return

    try:
        messages = [msg async for msg in channel.history(limit=limit)]
    except Exception as e:
        print(f"Error fetching messages in channel {channel.id}: {e}")
        return

    seen = defaultdict(list)
    duplicates = []

    for msg in messages:
        # This will group messages by their content
        seen[msg.content].append(msg)

    for msgs in seen.values():
        if len(msgs) > 1:
            duplicates.extend(msgs[1:])  # Skip the first occurrence, remove the rest

    for msg in duplicates:
        try:
            await msg.delete()
        except Exception as e:
            print(f"Failed to delete message: {e}")

    print(f"Removed {len(duplicates)} duplicate messages.")

bot.run(TOKEN)
