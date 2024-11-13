# Discord Bot Automatic SubReddit Posting
Discord bot using Reddit API for posting automatic SubReddit video's, GIF's and photo's in your Discord channels! ⭐

## Installation
1. Install Python libraries and set up server
```
# If running on server/VPS, I would recommend running in a screen sessions.
screen -RD reddit

# Clone repo
https://github.com/yZ1337/DiscordBot-Auto-SubReddit-Posting.git
cd DiscordBot-Auto-SubReddit-Posting

# Install Python libraries
pip install -r requirements.txt
```
2. Install the `database.sql` file into your database.

## How To Run
**Edit `.env` file first!**
Includes:
- Reddit API keys [Get them here](https://www.reddit.com/dev/api/)
- Database information
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
