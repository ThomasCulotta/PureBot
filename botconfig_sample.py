# Sample Bot Configuration
# Copy this file and customize for your Twitch bot

# Twitch channel name (without #)
twitchChannel = "<CHANNEL_NAME>"

# Bot's Twitch username
twitchUser = "<BOT_USERNAME>"

# Client app info
clientId = "<CLIENT_ID>"
clientSecret = "<CLIENT_SECRET>"

# Auth code to get OAuth token for
# Generate at: https://id.twitch.tv/oauth2/authorize?client_id=vvftu582whx7x4aetle0hgjn6gkt1g&redirect_uri=http://localhost&response_type=code&scope=chat:read+chat:edit+user:read:chat
authCode = "<AUTH_CODE>"

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
