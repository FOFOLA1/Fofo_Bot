import discord
from discord import app_commands, Interaction, Message, Embed, Color
from discord.ext import commands
from os import getenv
import logging
from aiohttp import ClientSession
from google import genai
from google.genai import types


GEMINI_API_KEY = getenv("GEMINI_API_KEY")


client = genai.Client()


async def call_gemini_api(text_input: str) -> str | None:
    # Safety check before calling API
    if not GEMINI_API_KEY:
        return "[Error: API Key is missing. Check your .env file]"

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

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
            ),
            contents=text_input,
        )
        return response.text
    except Exception as e:
        logging.error(f"Error calling Gemini API: {str(e)}")
        return f"Error occurred while calling Gemini API"


@app_commands.context_menu(name="De-Idiotize")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def deidiotize_context(interaction: Interaction, message: Message):
    logging.info(
        f"User: {interaction.user.name} ({interaction.user.id}) | Action: De-Idiotize | Target Message: {message.content!r} ({message.id})"
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
        if fixed_text:
            await interaction.followup.send(fixed_text)
        else:
            await interaction.followup.send(
                "❌ Failed to generate de-idiotized text.", ephemeral=True
            )

    except Exception as e:
        logging.error(f"Error in De-Idiotize: {str(e)}")
        await interaction.followup.send(
            f"Something went wrong: {str(e)}", ephemeral=True
        )


@app_commands.context_menu(name="De-Idiotize Ephemeral")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def deidiotize_context_ephemeral(interaction: Interaction, message: Message):
    logging.info(
        f"User: {interaction.user.name} ({interaction.user.id}) | Action: De-Idiotize Ephemeral | Target Message: {message.content!r} ({message.id})"
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
        if fixed_text:
            await interaction.followup.send(fixed_text)
        else:
            await interaction.followup.send(
                "❌ Failed to generate de-idiotized text.", ephemeral=True
            )

    except Exception as e:
        logging.error(f"Error in De-Idiotize Ephemeral: {str(e)}")
        await interaction.followup.send(
            f"Something went wrong: {str(e)}", ephemeral=True
        )


async def setup(bot: commands.Bot):
    bot.tree.add_command(deidiotize_context)
    bot.tree.add_command(deidiotize_context_ephemeral)
