import discord
from discord import app_commands, Interaction
from discord.ext import commands
from os import getenv
import logging

# Fetch variables
BOT_OWNER_ID = getenv("BOT_OWNER_ID")

# Convert owner ID to int if it exists, otherwise 0
if BOT_OWNER_ID and BOT_OWNER_ID.isdigit():
    BOT_OWNER_ID = int(BOT_OWNER_ID)
else:
    BOT_OWNER_ID = 0


def is_bot_owner(interaction: Interaction) -> bool:
    return interaction.user.id == BOT_OWNER_ID


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="restart", description="Restart the bot")
    @app_commands.check(is_bot_owner)
    async def restart_command(self, interaction: Interaction):
        logging.info(
            f"User: {interaction.user.name} ({interaction.user.id}) | Action: /restart | Target Message: N/A"
        )
        await interaction.response.send_message("Restarting...", ephemeral=True)
        await self.bot.close()

    @restart_command.error
    async def restart_command_error(self, interaction: Interaction, error):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message(
                "You must be the bot owner to do that!", ephemeral=True
            )
        else:
            logging.error(f"Error in restart command: {error}")
            await interaction.response.send_message(
                "An error occurred while restarting.", ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))
