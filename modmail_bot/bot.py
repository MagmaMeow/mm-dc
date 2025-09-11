import os
import sys
import discord
from discord.ext import commands
from discord import app_commands

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
intents.dm_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# Store thread/user mapping in-memory (for demo purposes)
user_threads = {}  # user_id -> thread_id

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
    try:
        await interaction.user.send("Please wait till someone comes back to you.")
        await interaction.response.send_message("We've sent you a DM. Please check your messages!", ephemeral=True)
    except Exception:
        await interaction.response.send_message("Failed to DM you. Please check your privacy settings.", ephemeral=True)

@bot.event
async def on_message(message):
    # If DM from user
    if isinstance(message.channel, discord.DMChannel) and not message.author.bot:
        guild = bot.get_guild(GUILD_ID)
        modmail_channel = guild.get_channel(MODMAIL_CHANNEL_ID)
        if not modmail_channel:
            await message.channel.send("Modmail channel not found. Please contact a moderator.")
            return

        # Create thread if not exists
        thread = None
        if message.author.id in user_threads:
            thread = await guild.fetch_channel(user_threads[message.author.id])
        if not thread:
            thread_message = await modmail_channel.send(f"Modmail from {message.author.mention} ({message.author.id})")
            thread = await modmail_channel.create_thread(name=f"Modmail: {message.author}", message=thread_message)
            user_threads[message.author.id] = thread.id

        await thread.send(f"**User:** {message.content}")

    # If message in a modmail thread from a mod
    elif hasattr(message.channel, "parent") and message.channel.parent and message.channel.parent.id == MODMAIL_CHANNEL_ID:
        # Find user by thread name
        user_id = None
        if message.channel.name.startswith("Modmail: "):
            user_name = message.channel.name[len("Modmail: "):]  
            # Try to resolve user id from mapping
            for uid, tid in user_threads.items():
                if tid == message.channel.id:
                    user_id = uid
                    break
        if user_id:
            user = await bot.fetch_user(user_id)
            if not message.author.bot:
                await user.send(f"**Mod:** {message.content}")

if __name__ == "__main__":
    bot.run(TOKEN)
    import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 2000))
    app.run(host="0.0.0.0", port=port)

# Start Flask server in a separate thread
threading.Thread(target=run_flask).start()
