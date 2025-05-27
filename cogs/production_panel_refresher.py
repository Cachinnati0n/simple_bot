import discord
from discord.ext import commands, tasks
from db import cursor, db_connection

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
                print(f"⚠️ Could not find thread {thread_id}")
                continue

            try:
                message = await thread.fetch_message(int(message_id))
            except discord.NotFound:
                print(f"⚠️ Panel message {message_id} not found in thread {thread_id}")
                continue

            # Get updated orders for this production order
            cursor.execute("""
                SELECT id, resource_name, amount, fulfilled_amount
                FROM GeneratedOrders
                WHERE production_order_id = %s AND status = 'open'
                ORDER BY created_at DESC;
            """, (production_id,))
            active_orders = cursor.fetchall()

            if not active_orders:
                await message.edit(content="📭 No active orders for this production.")
                continue

            # Rebuild message
            msg = "📦 Production Order Drop-Off Panel:\n\n"
            for order_id, res, amount, fulfilled in active_orders:
                percent = fulfilled / amount
                bar = "▰" * int(percent * 10) + "▱" * (10 - int(percent * 10))
                msg += f"✅ [`{order_id}`] `{res}` — {fulfilled}/{amount} ({percent:.1%}) {bar}\n"

            view = discord.ui.View(timeout=None)
            view.add_item(
                discord.ui.Button(label="Drop Off", style=discord.ButtonStyle.green, custom_id="dropoff_button")
            )

            await message.edit(content=msg, view=view)

    @refresh_panels.before_loop
    async def before_refresh(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(ProductionPanelRefresher(bot))