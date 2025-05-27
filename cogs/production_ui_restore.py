import discord
from discord.ext import commands
from db import cursor
from .productionorders import ProductionPanelView

class ProductionUIRestore(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.loop.create_task(self.restore_ui())

    async def restore_ui(self):
        await self.bot.wait_until_ready()
        cursor.execute("SELECT channel_id, message_id FROM ProductionUI")
        row = cursor.fetchone()
        if not row:
            return

        channel_id, message_id = int(row[0]), int(row[1])
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return

        try:
            message = await channel.fetch_message(message_id)
            await message.edit(view=ProductionPanelView(self.bot))
            print("✅ Reconnected ProductionPanelView to message.")
        except Exception as e:
            print(f"⚠️ Failed to reconnect view: {e}")

async def setup(bot):
    await bot.add_cog(ProductionUIRestore(bot))