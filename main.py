# import discord
from discord import Intents
from discord.ext import commands
from os import getenv
import logging
import signal
from dotenv import load_dotenv

# 1. Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    filename="bot_activity.log",
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# 2. Fetch variables
TOKEN = getenv("DISCORD_TOKEN")
GEMINI_API_KEY = getenv("GEMINI_API_KEY")


class FofoBot(commands.Bot):
    async def setup_hook(self):
        print("--- setup_hook started ---", flush=True)
        # Load extensions
        print("Loading cogs.admin...", flush=True)
        await self.load_extension("cogs.admin")
        print("Loading cogs.de_idiotize...", flush=True)
        await self.load_extension("cogs.de_idiotize")
        # Sync commands
        print("Syncing commands...", flush=True)
        await self.tree.sync()
        print("--- setup_hook finished ---", flush=True)


def main():
    intents = Intents.default()
    intents.message_content = True

    bot = FofoBot(command_prefix="/", intents=intents)

    @bot.event
    async def on_ready():
        # --- DEBUG PRINTS (Check your console when you run this!) ---
        print("--------------------------------------------------", flush=True)
        print(f"Logged in as: {bot.user} (ID: {bot.user.id})", flush=True)
        print(f"Discord Token Loaded: {'YES' if TOKEN else '❌ NO'}", flush=True)

        if GEMINI_API_KEY:
            # Print the first 4 chars to verify it's the right key, mask the rest
            masked_key = GEMINI_API_KEY[:4] + "..." + GEMINI_API_KEY[-4:]
            print(f"Gemini API Key Loaded: ✅ YES ({masked_key})", flush=True)
        else:
            print("Gemini API Key Loaded: ❌ NO (Check .env file)", flush=True)

        print("--------------------------------------------------", flush=True)

    if not TOKEN:
        print("CRITICAL ERROR: DISCORD_TOKEN is missing from .env file")
        return

    # Handle SIGTERM (Docker stop signal) to ensure graceful shutdown
    def signal_handler(sig, frame):
        logging.info("Received SIGTERM, shutting down...")
        print("\nReceived SIGTERM, shutting down...")
        # Raising KeyboardInterrupt allows bot.run() to handle the shutdown gracefully
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, signal_handler)

    bot.run(TOKEN)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}")
