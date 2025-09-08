import os
import discord
from discord.ext import commands
from discord import app_commands

TOKEN = os.getenv('TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))
MODMAIL_CHANNEL_ID = int(os.getenv('MODMAIL_CHANNEL_ID'))

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

# /modcall command: lets users open a modmail thread from the server, not just DM
@tree.command(name="modcall", description="Contact the moderators via modmail", guild=discord.Object(id=GUILD_ID))
async def modcall(interaction: discord.Interaction):
    modmail_channel = bot.get_channel(MODMAIL_CHANNEL_ID)
    if not modmail_channel:
        await interaction.response.send_message("Modmail channel not found.", ephemeral=True)
        return
    embed = discord.Embed(title="Modmail Request", description=f"{interaction.user.mention} has requested modmail.", color=discord.Color.blue())
    await modmail_channel.send(embed=embed)
    await interaction.response.send_message("Your modmail request has been sent to the moderators!", ephemeral=True)

# DM support: if a user DMs the bot, forward to modmail channel
@bot.event
async def on_message(message):
    # Ignore messages from bots and messages in servers
    if message.author.bot or message.guild:
        return
    # Forward DM to modmail channel
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