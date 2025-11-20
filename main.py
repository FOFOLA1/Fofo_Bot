# import discord
from discord import Intents, Interaction, app_commands, Embed, Color, Message
from discord.ext import commands
from os import getenv
import logging
from aiohttp import ClientSession
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
GOOGLE_API_KEY = getenv("GOOGLE_API_KEY")
BOT_OWNER_ID = getenv("BOT_OWNER_ID")

# Convert owner ID to int if it exists, otherwise 0
if BOT_OWNER_ID and BOT_OWNER_ID.isdigit():
    BOT_OWNER_ID = int(BOT_OWNER_ID)
else:
    BOT_OWNER_ID = 0

# URL without the key (we put the key in the header now)
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


def is_bot_owner(interaction: Interaction):
    return interaction.user.id == BOT_OWNER_ID


async def call_gemini_api(text_input: str):
    # Safety check before calling API
    if not GOOGLE_API_KEY:
        return "[Error: API Key is missing. Check your .env file]"

    # Headers - passing the key here is safer and more standard
    headers = {"Content-Type": "application/json", "x-goog-api-key": GOOGLE_API_KEY}

    system_prompt = (
        "You are a technical support editor. Your task is to rewrite the user's text into "
        "clear, concise, and grammatically correct standard language (keep the same language as input). "
        "Guidelines:\n"
        "1. Fix spelling, grammar, and punctuation.\n"
        "2. Remove slang, aggression, and excessive abbreviations.\n"
        "3. IDENTITY PRESERVATION (CRITICAL): Detect usernames, nicknames, exact error codes, or file paths. "
        "Keep them EXACTLY as they appear (case-sensitive) and WRAP THEM in single backticks (`). "
        "Example: 'user_name' -> `user_name`. This prevents Discord formatting issues.\n"
        "4. FORMATTING: Use Discord Markdown to improve readability where useful. "
        "Use **bold** for emphasis or key concepts. Use bullet points (*) if the input contains a list of items or steps.\n"
        "5. Output ONLY the rewritten text.\n\n"
        "Examples:\n"
        "Input: ahoj Pepik123 jak se mas\n"
        "Output: Ahoj `Pepik123`, jak se máš?\n"
        "Input: ban user xX_Destroyer_Xx pls because he griefed\n"
        "Output: Please ban user `xX_Destroyer_Xx` because he **griefed**.\n"
        "Input: mam problem nejde mi mc, pise to error 500 a nevim heslo\n"
        "Output: Mám problém:\n* Nejde mi **Minecraft**\n* Píše to `error 500`\n* Nevím heslo"
    )

    payload = {
        "contents": [
            {"parts": [{"text": f"{system_prompt}\n\nInput Text:\n{text_input}"}]}
        ]
    }

    async with ClientSession() as session:
        async with session.post(GEMINI_URL, headers=headers, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                return f"[API Error {response.status}]: {error_text}"

            result = await response.json()
            try:
                return result["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError):
                return "[Error: Unexpected response format from Google AI]"


def main():
    intents = Intents.default()
    intents.message_content = True

    bot = commands.Bot(command_prefix="/", intents=intents)

    @bot.event
    async def on_ready():
        await bot.tree.sync()

        # --- DEBUG PRINTS (Check your console when you run this!) ---
        print("--------------------------------------------------")
        print(f"Logged in as: {bot.user} (ID: {bot.user.id})")
        print(f"Discord Token Loaded: {'YES' if TOKEN else '❌ NO'}")

        if GOOGLE_API_KEY:
            # Print the first 4 chars to verify it's the right key, mask the rest
            masked_key = GOOGLE_API_KEY[:4] + "..." + GOOGLE_API_KEY[-4:]
            print(f"Google API Key Loaded: ✅ YES ({masked_key})")
        else:
            print("Google API Key Loaded: ❌ NO (Check .env file)")

        print("--------------------------------------------------")

    @bot.tree.command(name="restart", description="Restart the bot")
    @app_commands.check(is_bot_owner)
    async def restart_command(interaction: Interaction):
        logging.info(
            f"User: {interaction.user.name} ({interaction.user.id}) | Action: /restart | Target Message: N/A"
        )
        await interaction.response.send_message("Restarting...", ephemeral=True)
        await bot.close()

    @restart_command.error
    async def restart_command_error(interaction: Interaction, error):
        await interaction.response.send_message(
            "You must be the bot owner to do that!", ephemeral=True
        )

    @bot.tree.context_menu(name="De-idiotize")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def deidiotize_context(interaction: Interaction, message: Message):
        logging.info(
            f"User: {interaction.user.name} ({interaction.user.id}) | Action: De-idiotize | Target Message: {message.content!r} ({message.id})"
        )
        original_text = message.content

        if not original_text:
            await interaction.response.send_message(
                "❌ That message doesn't contain any text.", ephemeral=True
            )
            return

        await interaction.response.defer()

        try:
            fixed_text = await call_gemini_api(original_text)
            # embed = Embed(description=fixed_text, color=Color.blue())
            # embed.set_footer(text=f"Original by {message.author.display_name}")
            # await interaction.followup.send(embed=embed)
            await interaction.followup.send(fixed_text)

        except Exception as e:
            await interaction.followup.send(
                f"Something went wrong: {str(e)}", ephemeral=True
            )

    @bot.tree.context_menu(name="De-idiotize_Ephemeral")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def deidiotize_context_ephemeral(interaction: Interaction, message: Message):
        logging.info(
            f"User: {interaction.user.name} ({interaction.user.id}) | Action: De-idiotize_Ephemeral | Target Message: {message.content!r} ({message.id})"
        )
        original_text = message.content

        if not original_text:
            await interaction.response.send_message(
                "❌ That message doesn't contain any text.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        try:
            fixed_text = await call_gemini_api(original_text)
            embed = Embed(description=fixed_text, color=Color.blue())
            embed.set_footer(text=f"Original by {message.author.display_name}")
            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(
                f"Something went wrong: {str(e)}", ephemeral=True
            )

    if not TOKEN:
        print("CRITICAL ERROR: DISCORD_TOKEN is missing from .env file")
        return

    bot.run(TOKEN)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}")
