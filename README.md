# Discord Bot for posting automatic Reddit video's, GIF's and photo's

## Install libraries
```
# If running on server/VPS, I would recommend running in a screen sessions.
screen -RD reddit

pip install -r requirements.txt
```

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
