# Sample Bot Configuration
# Copy this file and customize for your Twitch bot

# Twitch channel name (without #)
twitchChannel = "<CHANNEL_NAME>"

# Bot's Twitch username
twitchUser = "<BOT_USERNAME>"

# Client app info
clientId = "<CLIENT_ID>"
clientSecret = "<CLIENT_SECRET>"

# OAuth token for authentication
# Generate at: https://twitchtokengenerator.com/
oauth = "oauth:<ACCESS_TOKEN>"

# Refresh at: https://twitchtokengenerator.com/api/refresh/<REFRESH_TOKEN>
refreshOauth = "<REFRESH_TOKEN>"

# Other api keys
spoonacularAuthKey = ""
igdbAuthKey = ""
steamAuthKey = ""
spotifyIdAndSecret = ""

# Twitch chat variables
scoreLifespan = 600
clearScoreId = ""
stealScoreId = ""
swapScoreId = ""

# MongoDB connection string
# Format: mongodb://[username:password@]host(:port)/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000
DbConnectionString = ""

# Command prefixes (list of single characters)
# Messages starting with these characters will trigger commands
prefixes = ['!']

# Command modules to exclude/disable
# Names should match the command module filenames in Commands/ directory
exclude = [
    # "PollCommands",
    # "DiceCommands",
    # "VoteBanCommands",
]

# Enable debug logging
debugLog = False
