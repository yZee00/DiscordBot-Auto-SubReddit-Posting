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

intents = discord.Intents.default()

TOKEN = os.getenv('DISCORD_BOT_TOKEN')

CLIENT_ID = os.getenv('CLIENT_ID')
SECRET = os.getenv('SECRET')
AGENT = os.getenv('AGENT')

USER = os.getenv('USER')
PASS = os.getenv('PASS')
DATABASE = os.getenv('DATABASE_REDDIT')

SCHEDULED_TIME = os.getenv('SCHEDULED_TIME')
GAMENAME = os.getenv('GAMENAME')

reddit = mysql.connector.connect(
    host="localhost",
    user= USER,
    password= PASS,
    database= DATABASE
)
print("redditDB: " + str(reddit))

redditDB = reddit.cursor()

bot = commands.Bot(command_prefix='!!!', help_command=None, intents=intents)

allowed_role_ids = [CHANGE THIS HERE]

restricted_channels = [CHANGE THIS HERE]

last_posted_url = {}

def ensure_connection():
    try:
        reddit.ping(reconnect=True, attempts=3, delay=5)
    except mysql.connector.Error as err:
        print(f"Error while reconnecting to the database: {err}")

@tasks.loop(hours=SCHEDULED_TIME)
async def scheduled_task():
    reddit = asyncpraw.Reddit(client_id=CLIENT_ID, client_secret=SECRET, user_agent=AGENT)
    channel_private = bot.get_channel(CHANGE THIS HERE)
    try:
        ensure_connection()
        await channel_private.send("Running scheduled task!")
        redditDB.execute("SELECT subreddit, channel_id FROM sub_channel")
        rows = redditDB.fetchall()
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
    if message.author == bot.user:
        return

    if message.channel.id in restricted_channels:
        user_roles = [role.id for role in message.author.roles]
        if any(role in user_roles for role in allowed_role_ids):
            pass
        else:
            if re.search(r'(discord\.gg\/[a-zA-Z0-9]+)|(t\.me\/[a-zA-Z0-9]+)|(telegram\.me\/[a-zA-Z0-9]+)|(discord\.com\/[a-zA-Z0-9]+)|(signal\.com\/[a-zA-Z0-9]+)', message.content):
                await message.delete()
                print(f"User {message.author} banned for posting links")
                try:
                    await message.author.ban(reason="Posting prohibited links")
                except discord.Forbidden:
                    print(f"I don't have permissions to ban {message.author.name}")
                except discord.HTTPException as e:
                    print(f"Failed to ban {message.author.name}: {str(e)}")
    
    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    if not scheduled_task.is_running():
        scheduled_task.start()
    await bot.change_presence(activity=discord.Game(name=GAMENAME))

@bot.command(name='monitor')
async def monitor(ctx, subreddit_name: str, discord_channel_id: int):
    if any(role.id in allowed_role_ids for role in ctx.author.roles):
        reddit = asyncpraw.Reddit(client_id=CLIENT_ID, client_secret=SECRET, user_agent=AGENT)
        try:
            ensure_connection()
            redditDB.execute("SELECT * FROM sub_channel WHERE subreddit = %s AND channel_id = %s",
                                (subreddit_name, discord_channel_id))
            if redditDB.fetchone():
                await ctx.send("This subreddit is already being monitored in the specified channel.")
                return

            redditDB.execute("INSERT INTO sub_channel (subreddit, channel_id) VALUES (%s, %s)",
                                (subreddit_name, discord_channel_id))
            reddit.commit()
            await ctx.send("Subreddit successfully added to the monitoring list.")
        except mysql.connector.Error as err:
            print(f"Database error: {err}")
            await ctx.send("Failed to save to the database.")
            return

        url = await check_reddit(reddit, subreddit_name, discord_channel_id)
        if url:
            channel = bot.get_channel(discord_channel_id)
            if url.endswith('.mp4'):
                await channel.send(file=discord.File(url))
                os.remove(url)
            else:
                if channel:
                    await channel.send(url)
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
            redditDB.execute("SELECT subreddit, channel_id FROM sub_channel")
            rows = redditDB.fetchall()
            for subreddit_name, discord_channel_id in rows:
                result = await check_reddit(reddit, subreddit_name, discord_channel_id)
                if result:
                    channel = bot.get_channel(int(discord_channel_id))
                    if channel:
                        if result.endswith('.mp4'):
                            await channel.send(file=discord.File(result))
                            os.remove(result)
                        else:
                            await channel.send(result)
                    await auto_remove_duplicates(channel)
            await ctx.send("Latest posts have been sent.")
        except mysql.connector.Error as err:
            print(f"Failed to fetch data from the database: {err}")
        except Exception as e:
            print(f"[ERROR] | {e}")

@bot.command(name='removeduplicates', help='Remove duplicate messages in a channel')
@commands.has_permissions(manage_messages=True)
async def remove_duplicates(ctx, limit: int = 10):
    if limit > 1000:
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
        seen[msg.content].append(msg)

    for msgs in seen.values():
        if len(msgs) > 1:
            duplicates.extend(msgs[1:])

    for msg in duplicates:
        try:
            await msg.delete()
        except Exception as e:
            print(f"Failed to delete message: {e}")

    print(f"Removed {len(duplicates)} duplicate messages.")

async def auto_remove_duplicates(channel, limit=10):
    if not channel:
        print("auto_remove_duplicates: Channel is None")
        return

    if limit > 1000:
        print("Limit is too high. Please use a number less than or equal to 1000.")
        return

    try:
        messages = [msg async for msg in channel.history(limit=limit)]
    except Exception as e:
        print(f"Error fetching messages in channel {channel.id if channel else 'Unknown'}: {e}")
        return

    seen = defaultdict(list)
    duplicates = []

    for msg in messages:
        seen[msg.content].append(msg)

    for msgs in seen.values():
        if len(msgs) > 1:
            duplicates.extend(msgs[1:])

    for msg in duplicates:
        try:
            await msg.delete()
        except Exception as e:
            print(f"Failed to delete message: {e}")

    print(f"Removed {len(duplicates)} duplicate messages.")


bot.run(TOKEN)
