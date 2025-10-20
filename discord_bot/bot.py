#!/usr/bin/env python3
"""
SampleMind AI Discord Bot
Community engagement, support, and showcase features
"""

import os
import asyncio
from datetime import datetime
from typing import Optional
import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiohttp

# Bot configuration
DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GITHUB_REPO = "lchtangen/samplemind-ai"
PYPI_PACKAGE = "samplemind-ai"

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    """Bot startup"""
    print(f'🤖 {bot.user} is now online!')
    print(f'📊 Serving {len(bot.guilds)} servers')
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f'✅ Synced {len(synced)} slash commands')
    except Exception as e:
        print(f'❌ Failed to sync commands: {e}')
    
    # Start background tasks
    update_stats.start()
    
    # Set bot status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="music producers create magic 🎵"
        )
    )


@bot.event
async def on_member_join(member: discord.Member):
    """Welcome new members"""
    welcome_embed = discord.Embed(
        title=f"Welcome to SampleMind AI, {member.name}! 🎵",
        description="Let's get you started on your AI-powered music production journey!",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow()
    )
    
    welcome_embed.add_field(
        name="📦 Step 1: Install",
        value="```bash\npip install samplemind-ai\n```",
        inline=False
    )
    
    welcome_embed.add_field(
        name="📚 Step 2: Learn",
        value="Check out <#DOCS_CHANNEL_ID> for guides and tutorials",
        inline=False
    )
    
    welcome_embed.add_field(
        name="💬 Step 3: Introduce Yourself",
        value="Head to <#INTRODUCTIONS_CHANNEL_ID> and say hi!",
        inline=False
    )
    
    welcome_embed.add_field(
        name="🆘 Need Help?",
        value="Use `/help` to see all available commands",
        inline=False
    )
    
    welcome_embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    welcome_embed.set_footer(text="SampleMind AI Community", icon_url=bot.user.avatar.url)
    
    # Send DM
    try:
        await member.send(embed=welcome_embed)
    except discord.Forbidden:
        # If DM fails, send to welcome channel
        welcome_channel = discord.utils.get(member.guild.channels, name='welcome')
        if welcome_channel:
            await welcome_channel.send(f"{member.mention}", embed=welcome_embed)


@bot.tree.command(name="help", description="Show all available commands")
async def help_command(interaction: discord.Interaction):
    """Display help information"""
    help_embed = discord.Embed(
        title="🤖 SampleMind AI Bot Commands",
        description="Here are all the commands you can use:",
        color=discord.Color.blue()
    )
    
    help_embed.add_field(
        name="📊 /stats",
        value="View live project statistics",
        inline=False
    )
    
    help_embed.add_field(
        name="🎨 /showcase",
        value="Submit your SampleMind creation",
        inline=False
    )
    
    help_embed.add_field(
        name="📚 /docs",
        value="Get links to documentation",
        inline=False
    )
    
    help_embed.add_field(
        name="🐛 /report",
        value="Report a bug or issue",
        inline=False
    )
    
    help_embed.add_field(
        name="💡 /feature",
        value="Request a new feature",
        inline=False
    )
    
    help_embed.add_field(
        name="🎯 /quickstart",
        value="Get started with SampleMind AI",
        inline=False
    )
    
    await interaction.response.send_message(embed=help_embed)


@bot.tree.command(name="stats", description="View live SampleMind AI statistics")
async def stats_command(interaction: discord.Interaction):
    """Display project statistics"""
    await interaction.response.defer()
    
    try:
        # Fetch GitHub stats
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://api.github.com/repos/{GITHUB_REPO}') as resp:
                if resp.status == 200:
                    github_data = await resp.json()
                    stars = github_data.get('stargazers_count', 0)
                    forks = github_data.get('forks_count', 0)
                    watchers = github_data.get('subscribers_count', 0)
                    issues = github_data.get('open_issues_count', 0)
                else:
                    stars = forks = watchers = issues = "N/A"
            
            # Fetch PyPI stats (if available)
            try:
                async with session.get(f'https://api.pepy.tech/api/v2/projects/{PYPI_PACKAGE}') as resp:
                    if resp.status == 200:
                        pypi_data = await resp.json()
                        downloads = pypi_data.get('total_downloads', 0)
                    else:
                        downloads = "N/A"
            except:
                downloads = "Coming soon"
        
        stats_embed = discord.Embed(
            title="📊 SampleMind AI Live Stats",
            description="Real-time project metrics",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        stats_embed.add_field(name="⭐ GitHub Stars", value=str(stars), inline=True)
        stats_embed.add_field(name="🍴 Forks", value=str(forks), inline=True)
        stats_embed.add_field(name="👀 Watchers", value=str(watchers), inline=True)
        stats_embed.add_field(name="📦 PyPI Downloads", value=str(downloads), inline=True)
        stats_embed.add_field(name="🐛 Open Issues", value=str(issues), inline=True)
        stats_embed.add_field(name="👥 Discord Members", value=str(interaction.guild.member_count), inline=True)
        
        stats_embed.set_footer(text="Updated just now", icon_url=bot.user.avatar.url)
        
        await interaction.followup.send(embed=stats_embed)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Failed to fetch stats: {str(e)}")


@bot.tree.command(name="showcase", description="Submit your SampleMind creation")
async def showcase_command(interaction: discord.Interaction):
    """Submit a showcase"""
    showcase_embed = discord.Embed(
        title="🎨 Share Your SampleMind Creation!",
        description="We'd love to see what you've made!",
        color=discord.Color.purple()
    )
    
    showcase_embed.add_field(
        name="How to Submit:",
        value=(
            "1. Upload your screenshot/video\n"
            "2. Describe what you created\n"
            "3. Tag your post with `#showcase`\n"
            "4. Get featured on our social media!"
        ),
        inline=False
    )
    
    showcase_embed.add_field(
        name="What to Include:",
        value=(
            "• Screenshot of your analysis\n"
            "• Description of your workflow\n"
            "• Any tips or tricks you discovered\n"
            "• Your social media handle (optional)"
        ),
        inline=False
    )
    
    await interaction.response.send_message(embed=showcase_embed)


@bot.tree.command(name="docs", description="Get documentation links")
async def docs_command(interaction: discord.Interaction):
    """Provide documentation links"""
    docs_embed = discord.Embed(
        title="📚 SampleMind AI Documentation",
        description="Everything you need to know",
        color=discord.Color.blue()
    )
    
    docs_embed.add_field(
        name="📖 User Guide",
        value="[Read the User Guide](https://docs.samplemind.ai/user-guide)",
        inline=False
    )
    
    docs_embed.add_field(
        name="💻 Developer Guide",
        value="[Developer Documentation](https://docs.samplemind.ai/developer-guide)",
        inline=False
    )
    
    docs_embed.add_field(
        name="🔧 API Reference",
        value="[API Documentation](https://docs.samplemind.ai/api)",
        inline=False
    )
    
    docs_embed.add_field(
        name="🚀 Quick Start",
        value="[Getting Started Guide](https://docs.samplemind.ai/quickstart)",
        inline=False
    )
    
    docs_embed.add_field(
        name="📦 GitHub Repository",
        value=f"[View on GitHub](https://github.com/{GITHUB_REPO})",
        inline=False
    )
    
    await interaction.response.send_message(embed=docs_embed)


@bot.tree.command(name="quickstart", description="Get started with SampleMind AI")
async def quickstart_command(interaction: discord.Interaction):
    """Quick start guide"""
    quickstart_embed = discord.Embed(
        title="🚀 Quick Start Guide",
        description="Get up and running in 5 minutes!",
        color=discord.Color.green()
    )
    
    quickstart_embed.add_field(
        name="1️⃣ Install",
        value="```bash\npip install samplemind-ai\n```",
        inline=False
    )
    
    quickstart_embed.add_field(
        name="2️⃣ Run",
        value="```bash\nsamplemind\n```",
        inline=False
    )
    
    quickstart_embed.add_field(
        name="3️⃣ Analyze",
        value="Select option 1 to analyze your first sample!",
        inline=False
    )
    
    quickstart_embed.add_field(
        name="Need Help?",
        value="Ask in <#SUPPORT_CHANNEL_ID> or use `/help`",
        inline=False
    )
    
    await interaction.response.send_message(embed=quickstart_embed)


@tasks.loop(hours=24)
async def update_stats():
    """Daily stats update"""
    # This would post daily stats to a designated channel
    pass


@bot.event
async def on_message(message: discord.Message):
    """Handle messages"""
    if message.author.bot:
        return
    
    # Auto-respond to common questions
    content_lower = message.content.lower()
    
    if "how to install" in content_lower or "installation" in content_lower:
        await message.reply(
            "📦 To install SampleMind AI:\n```bash\npip install samplemind-ai\n```\n"
            "For more details, use `/quickstart`"
        )
    
    elif "not working" in content_lower or "error" in content_lower:
        await message.reply(
            "🐛 Having issues? Please use `/report` to submit a bug report, "
            "or check <#SUPPORT_CHANNEL_ID> for help!"
        )
    
    # Process commands
    await bot.process_commands(message)


def main():
    """Run the bot"""
    if not DISCORD_TOKEN:
        print("❌ DISCORD_BOT_TOKEN environment variable not set!")
        print("Please set it in your .env file or environment")
        return
    
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")


if __name__ == "__main__":
    main()

