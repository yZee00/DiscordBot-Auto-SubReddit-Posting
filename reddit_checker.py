import asyncpraw
import aiohttp
import os
import discord
from collections import defaultdict
from moviepy.editor import *

# Global variable for the last posted URL
last_posted_url = {}

async def download_and_combine_video(video_url, audio_url, filename):
    video_filename = f"{filename}_video.mp4"

    video_success = await download_file(video_url, video_filename)

    if not video_success:
        print("Failed to download video")
        return None

    audio_success = await download_file(audio_url, f"{filename}_audio.mp4")

    if audio_success:
        # Combine video and audio
        final_filename = f"{filename}.mp4"
        video_clip = VideoFileClip(video_filename)
        audio_clip = AudioFileClip(f"{filename}_audio.mp4")
        final_clip = video_clip.set_audio(audio_clip)
        final_clip.write_videofile(final_filename, codec="libx264", audio_codec="aac")

        video_clip.close()
        audio_clip.close()
        os.remove(video_filename)
        os.remove(f"{filename}_audio.mp4")
        return final_filename
    else:
        # No audio found, return video file as is
        return video_filename


async def get_file_size(url):
    async with aiohttp.ClientSession() as session:
        async with session.head(url) as response:
            if response.status == 200:
                return int(response.headers.get('Content-Length', 0))
            else:
                return 0

async def download_file(url, filename):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                with open(filename, 'wb') as f:
                    while True:
                        chunk = await resp.content.read(1024)
                        if not chunk:
                            break
                        f.write(chunk)
                return True
            else:
                print(f"Failed to download: {url}, Status Code: {resp.status}")
                return False

                        
async def check_reddit(reddit, subreddit_name, channel_id):
    global last_posted_url
    try:
        subreddit = await reddit.subreddit(subreddit_name, fetch=True)
        async for new_post in subreddit.new(limit=5):
            if new_post.url != last_posted_url.get(subreddit_name, '') and 'pornofword.com' not in new_post.url:
                if new_post.is_video and new_post.media['reddit_video']['is_gif'] == False:
                    video_url = new_post.media['reddit_video']['fallback_url']
                    audio_url = video_url.split("DASH_")[0] + "DASH_audio.mp4"

                    # Check if file size is within limits
                    video_size = await get_file_size(video_url)
                    audio_size = await get_file_size(audio_url)
                    total_size = video_size + audio_size

                    if total_size > 0 and total_size <= 25 * 1024 * 1024:
                        filename = await download_and_combine_video(video_url, audio_url, f"temp_video_{subreddit_name}")
                        if filename:
                            last_posted_url[subreddit_name] = new_post.url
                            return filename
                        else:
                            # Skip if download failed
                            return None

                elif any(ext in new_post.url for ext in ['.jpg', '.jpeg', '.png', '.gif', 'imgur', 'redgifs']):
                    last_posted_url[subreddit_name] = new_post.url
                    return new_post.url
    except Exception as e:
        print(f"An error occurred in check_reddit for subreddit {subreddit_name}: {e}")
        return None

async def scheduled_check(reddit, bot, subreddit_name, discord_channel_id):
    try:
        result = await check_reddit(reddit, subreddit_name, discord_channel_id)
        if result:
            channel = bot.get_channel(discord_channel_id)
            if channel:
                # Check if the result is a filename (for videos)
                if result.endswith('.mp4'):
                    await channel.send(file=discord.File(result))
                    os.remove(result)  # Remove the file after sending
                else:
                    await channel.send(result)  # Send the URL for images and gifs
    except Exception as e:
        print(f"An error occurred in scheduled_check: {e}")
