import os
import sys
import discord
from discord.ext import commands
from discord import app_commands

# Fetch environment variables safely
TOKEN = os.getenv('TOKEN')
GUILD_ID = os.getenv('GUILD_ID')
MODMAIL_CHANNEL_ID = os.getenv('MODMAIL_CHANNEL_ID')

missing_vars = []
if not TOKEN:
    missing_vars.append('TOKEN')
if not GUILD_ID:
    missing_vars.append('GUILD_ID')
if not MODMAIL_CHANNEL_ID:
    missing_vars.append('MODMAIL_CHANNEL_ID')

if missing_vars:
    print(f"ERROR: Missing environment variables: {', '.join(missing_vars)}. Please set them in your Render dashboard or .env file.")
    sys.exit(1)

try:
    GUILD_ID = int(GUILD_ID)
    MODMAIL_CHANNEL_ID = int(MODMAIL_CHANNEL_ID)
except ValueError:
    print("ERROR: GUILD_ID and MODMAIL_CHANNEL_ID must be integers. Please check your environment variables.")
    sys.exit(1)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@tree.command(name="modcall", description="Contact the moderators via modmail", guild=discord.Object(id=GUILD_ID))
async def modcall(interaction: discord.Interaction):
    modmail_channel = bot.get_channel(MODMAIL_CHANNEL_ID)
    if not modmail_channel:
        await interaction.response.send_message("Modmail channel not found.", ephemeral=True)
        return
    embed = discord.Embed(title="Modmail Request", description=f"{interaction.user.mention} has requested modmail.", color=discord.Color.blue())
    await modmail_channel.send(embed=embed)
    await interaction.response.send_message("Your modmail request has been sent to the moderators!", ephemeral=True)

@bot.event
async def on_message(message):
    if message.author.bot or message.guild:
        return
    modmail_channel = bot.get_channel(MODMAIL_CHANNEL_ID)
    if modmail_channel:
        embed = discord.Embed(title="Modmail Message", description=message.content, color=discord.Color.green())
        embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
        await modmail_channel.send(embed=embed)
        await message.channel.send("Your message has been sent to the moderators!")
    else:
        await message.channel.send("Modmail channel not found. Please contact a moderator.")

if __name__ == "__main__":
    bot.run(TOKEN)