# Discord Bot Automatic SubReddit Posting
Discord bot using Reddit API for posting automatic SubReddit video's, GIF's and photo's in your Discord channels! ⭐

## Installation
1. Install Python libraries and set up server
```
# If running on server/VPS, I would recommend running in a screen session.
screen -RD reddit

# Clone repo
https://github.com/yZ1337/DiscordBot-Auto-SubReddit-Posting.git
cd DiscordBot-Auto-SubReddit-Posting

# Create a venv
python3 -m venv venv

# Activate venv
source venv/bin/activate

# Install Python libraries
pip3 install -r requirements.txt
```
2. Load the `database.sql` file into your database.

## How To Run
**Edit `.env` file first!**
Includes:
- Reddit API keys [Get them here]([[https://www.reddit.com/dev/api/](https://www.reddit.com/prefs/apps/?solution=30612ad914ef42d330612ad914ef42d3&js_challenge=1&token=54dba411ecc9fd270bca6277dc2a436123031c4895d451a3688276065b564b27)](https://www.reddit.com/prefs/apps))
- Database information

RUN! :)
```
python3 reddit.py
```

## How To Use in Discord
```
# Add subreddits for automatic posting in specified channel
!!!monitor SUBREDDIT_NAME CHANNEL_ID

# Manual posting in all channels from DB
!!!postlatest
```
