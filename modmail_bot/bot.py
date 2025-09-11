import os
import sys
import discord
from discord.ext import commands
from discord import app_commands
from flask import Flask
import threading

# --- Environment Variables ---
TOKEN = os.getenv('TOKEN')
GUILD_ID = os.getenv('GUILD_ID')
MODMAIL_CHANNEL_ID = os.getenv('MODMAIL_CHANNEL_ID')

# --- Check environment variables ---
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
    print("ERROR: GUILD_ID and MODMAIL_CHANNEL_ID must be integers.")
    sys.exit(1)

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents)
tree = bot.tree

# --- In-memory user-thread mapping ---
user_threads = {}  # user_id -> thread_id

# --- Discord Events ---
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.event
async def on_message(message):
    # Ignore bot messages
    if message.author.bot:
        return

    # DM from user
    if isinstance(message.channel, discord.DMChannel):
        guild = bot.get_guild(GUILD_ID)
        modmail_channel = guild.get_channel(MODMAIL_CHANNEL_ID)
        if not modmail_channel:
            await message.channel.send("Modmail channel not found. Please contact a moderator.")
            return

        # Create thread if not exists
        thread = None
        if message.author.id in user_threads:
            try:
                thread = await guild.fetch_channel(user_threads[message.author.id])
            except:
                pass

        if not thread:
            thread_message = await modmail_channel.send(f"Modmail from {message.author.mention} ({message.author.id})")
            thread = await modmail_channel.create_thread(
                name=f"Modmail: {message.author}",
                message=thread_message
            )
            user_threads[message.author.id] = thread.id

        await thread.send(f"**User:** {message.content}")

    # Message in modmail thread from mod
    elif hasattr(message.channel, "parent") and message.channel.parent and message.channel.parent.id == MODMAIL_CHANNEL_ID:
        # Find user by thread
        user_id = None
        for uid, tid in user_threads.items():
            if tid == message.channel.id:
                user_id = uid
                break
        if user_id:
            try:
                user = await bot.fetch_user(user_id)
                await user.send(f"**Mod:** {message.content}")
            except discord.Forbidden:
                pass

    # Ensure commands still work
    await bot.process_commands(message)

# --- Slash Commands ---
@tree.command(
    name="modcall",
    description="Contact the moderators via modmail",
    guild=discord.Object(id=GUILD_ID)
)
async def modcall(interaction: discord.Interaction):
    try:
        await interaction.user.send("Please wait till someone comes back to you.")
        await interaction.response.send_message("We've sent you a DM. Please check your messages!", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("Failed to DM you. Please check your privacy settings.", ephemeral=True)

@tree.command(
    name="close",
    description="Close the current modmail thread",
    guild=discord.Object(id=GUILD_ID)
)
async def close(interaction: discord.Interaction):
    channel = interaction.channel

    # Only allow inside threads under modmail channel
    if not isinstance(channel, discord.Thread) or not channel.parent or channel.parent.id != MODMAIL_CHANNEL_ID:
        await interaction.response.send_message("This command can only be used inside a modmail thread.", ephemeral=True)
        return

    # Find the user
    user_id = None
    for uid, tid in user_threads.items():
        if tid == channel.id:
            user_id = uid
            break

    # Notify the user
    if user_id:
        try:
            user = await bot.fetch_user(user_id)
            await user.send("Your modmail thread has been closed by a moderator. Thank you!")
        except discord.Forbidden:
            pass
        # Remove mapping
        del user_threads[user_id]

    # Archive and lock the thread
    await channel.send("This modmail thread has been closed. The thread will be archived.")
    await channel.edit(archived=True, locked=True)

    # Confirm to moderator
    await interaction.response.send_message("Thread successfully closed.", ephemeral=True)

# --- Flask Keep-Alive ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 2000))
    app.run(host="0.0.0.0", port=port)

# --- Start Flask in a separate thread ---
threading.Thread(target=run_flask).start()

# --- Run the bot ---
bot.run(TOKEN)
