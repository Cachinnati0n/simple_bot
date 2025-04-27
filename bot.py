# bot.py

import os
import discord
from discord.ext import commands
from datetime import datetime
import asyncio
from db import cursor, db_connection, initialize_tables
from utils import calculate_next_run
from cogs.dropoff_ui import DropoffPanelView

intents = discord.Intents.default()
intents.message_content = True

class FoxholeBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents, help_command=None)


    async def setup_hook(self):
        initialize_tables()
        # Load cogs here
        await self.load_extension("cogs.neworder")
        await self.load_extension("cogs.ping")
        await self.load_extension("cogs.dropoff")
        await self.load_extension("cogs.orders")
        await self.load_extension("cogs.mydrops")
        await self.load_extension("cogs.completedorders")
        await self.load_extension("cogs.ordercontrol")
        await self.load_extension("cogs.status")
        await self.load_extension("cogs.help")
        await self.load_extension("cogs.dropoff_ui")
        await self.load_extension("cogs.orderonce")



        self.add_view(DropoffPanelView(self))  # Persistent view on restart



        #await self.load_extension("cogs.setchannel")

        # Start background task
        self.bg_task = self.loop.create_task(self.order_scheduler())

    async def on_ready(self):
        print(f"✅ Logged in as {self.user}")

    async def order_scheduler(self):
        await self.wait_until_ready()
        while not self.is_closed():
            try:
                now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

                cursor.execute("""
                    SELECT * FROM RecurringOrders
                    WHERE next_run_time <= %s AND active = TRUE;
                """, (now,))
                due_orders = cursor.fetchall()

                for order in due_orders:
                    id, user_id, server_id, resource_name, amount, recurrence, next_run, channel_id, active = order

                    guild = self.get_guild(int(server_id))
                    channel = guild.get_channel(int(channel_id)) if guild else None

                    if not channel:
                        print(f"⚠️ Could not find channel ID {channel_id}")
                        continue

                    await channel.send(
                        f"📦 **New Order Posted!**\n"
                        f"Resource: `{resource_name}`\n"
                        f"Target Amount: `{amount}`\n"
                        f"Drop-offs accepted below."
                    )

                    cursor.execute("""
                        INSERT INTO GeneratedOrders (
                            recurring_order_id, user_id, server_id, resource_name,
                            amount, fulfilled_amount, channel_id
                        ) VALUES (%s, %s, %s, %s, %s, 0, %s);
                    """, (
                        id, user_id, server_id, resource_name, amount, channel_id
                    ))

                    new_next = calculate_next_run(recurrence).strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute("""
                        UPDATE RecurringOrders SET next_run_time = %s WHERE id = %s;
                    """, (new_next, id))

                    db_connection.commit()

            except Exception as e:
                print(f"❌ Scheduler error: {e}")

            await asyncio.sleep(60)  # run every 60 seconds

# Instantiate and run the bot
bot = FoxholeBot()
bot.run(os.getenv("DISCORD_TOKEN"))
