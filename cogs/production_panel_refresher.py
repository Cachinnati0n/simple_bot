import discord
from discord.ext import commands, tasks
from db import cursor, db_connection
from cogs import productionthreadpanel  # Reuse central logic

class ProductionPanelRefresher(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.refresh_panels.start()

    def cog_unload(self):
        self.refresh_panels.cancel()

    @tasks.loop(minutes=2)
    async def refresh_panels(self):
        cursor.execute("SELECT production_order_id, thread_id, message_id FROM ProductionPanels")
        panels = cursor.fetchall()

        for production_id, thread_id, message_id in panels:
            thread = self.bot.get_channel(int(thread_id))
            if not thread:
                print(f"⚠️ Could not find thread {thread_id}, removing stale panel entry.")
                cursor.execute("DELETE FROM ProductionPanels WHERE thread_id = %s", (str(thread_id),))
                db_connection.commit()
                continue

            try:
                await productionthreadpanel.refresh_panel(self.bot, int(production_id))
            except Exception as e:
                print(f"⚠️ Failed to refresh panel for production {production_id}: {e}")

    @refresh_panels.before_loop
    async def before_refresh(self):
        await self.bot.wait_until_ready()

    async def refresh_single_panel(self, production_order_id: int):
        try:
            await productionthreadpanel.refresh_panel(self.bot, int(production_order_id))
        except Exception as e:
            print(f"⚠️ Failed to manually refresh panel for production {production_order_id}: {e}")


async def setup(bot):
    await bot.add_cog(ProductionPanelRefresher(bot))
