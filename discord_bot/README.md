# SampleMind AI Discord Bot

Community engagement bot for the SampleMind AI Discord server.

## Features

- 🎉 **Welcome Messages**: Greet new members with installation instructions
- 📊 **Live Stats**: Display GitHub stars, PyPI downloads, and community metrics
- 🎨 **Showcase System**: Let users share their creations
- 📚 **Documentation Links**: Quick access to all docs
- 🆘 **Auto-Support**: Respond to common questions
- 🏆 **Achievement Tracking**: Celebrate community milestones

## Setup

### 1. Create Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
3. Name it "SampleMind AI Bot"
4. Go to "Bot" section
5. Click "Add Bot"
6. Enable these Privileged Gateway Intents:
   - Server Members Intent
   - Message Content Intent
7. Copy the bot token

### 2. Install Dependencies

```bash
cd discord_bot
pip install -r requirements.txt
```

### 3. Configure Environment

Create a `.env` file:

```bash
DISCORD_BOT_TOKEN=your_bot_token_here
```

### 4. Invite Bot to Server

1. Go to "OAuth2" > "URL Generator"
2. Select scopes:
   - `bot`
   - `applications.commands`
3. Select bot permissions:
   - Send Messages
   - Embed Links
   - Attach Files
   - Read Message History
   - Use Slash Commands
4. Copy the generated URL and open it in your browser
5. Select your server and authorize

### 5. Run the Bot

```bash
python bot.py
```

## Commands

### Slash Commands

- `/help` - Show all available commands
- `/stats` - View live project statistics
- `/showcase` - Submit your SampleMind creation
- `/docs` - Get documentation links
- `/quickstart` - Quick start guide

### Auto-Responses

The bot automatically responds to:
- "how to install" → Installation instructions
- "not working" / "error" → Bug report guidance

## Customization

### Update Channel IDs

Replace placeholder channel IDs in `bot.py`:

```python
# Find and replace these:
DOCS_CHANNEL_ID
INTRODUCTIONS_CHANNEL_ID
SUPPORT_CHANNEL_ID
```

### Add Custom Commands

```python
@bot.tree.command(name="your_command", description="Description")
async def your_command(interaction: discord.Interaction):
    await interaction.response.send_message("Response")
```

## Deployment

### Option 1: Local Server

Run the bot on your local machine or server:

```bash
nohup python bot.py &
```

### Option 2: Cloud Hosting

Deploy to platforms like:
- **Railway**: Easy deployment with GitHub integration
- **Heroku**: Free tier available
- **DigitalOcean**: $5/month droplet
- **AWS EC2**: Free tier for 12 months

### Option 3: Docker

```bash
docker build -t samplemind-bot .
docker run -d --env-file .env samplemind-bot
```

## Monitoring

The bot logs to console. For production, consider:
- Setting up logging to file
- Using a process manager (PM2, systemd)
- Monitoring uptime with UptimeRobot

## Support

For issues with the bot:
- Check bot logs
- Verify token is correct
- Ensure intents are enabled
- Check bot permissions in server

## License

MIT License - Same as SampleMind AI

