import discord
from discord.ext import commands
from discord.utils import get
from db import cursor, db_connection
from utils import calculate_next_run
from datetime import datetime


class NewOrder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def neworder(self, ctx, amount: int, resource: str, recurrence: str, *, channel: str):
        try:
            channel_obj = get(ctx.guild.text_channels, mention=channel) or \
                        get(ctx.guild.text_channels, name=channel.strip("#"))

            if not channel_obj:
                await ctx.send("❌ Couldn't find that channel.")
                return

            now = datetime.utcnow()
            next_run = calculate_next_run(recurrence)

            # Step 1: Insert Recurring Order
            cursor.execute("""
                INSERT INTO RecurringOrders (user_id, server_id, resource_name, amount, recurrence, next_run_time, channel_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (
                str(ctx.author.id),
                str(ctx.guild.id),
                resource,
                amount,
                recurrence,
                next_run.strftime('%Y-%m-%d %H:%M:%S'),
                str(channel_obj.id)
            ))
            db_connection.commit()

            # Step 2: Fetch the ID of the new recurring order
            cursor.execute("SELECT LAST_INSERT_ID();")
            (recurring_id,) = cursor.fetchone()

            # Step 3: Post the first order immediately
            await channel_obj.send(
                f"📦 **New Order Posted!**\n"
                f"Resource: `{resource}`\n"
                f"Target Amount: `{amount}`\n"
                f"Drop-offs accepted below."
            )

            cursor.execute("""
                INSERT INTO GeneratedOrders (
                    recurring_order_id, user_id, server_id, resource_name,
                    amount, fulfilled_amount, channel_id
                ) VALUES (%s, %s, %s, %s, %s, 0, %s);
            """, (
                recurring_id,
                str(ctx.author.id),
                str(ctx.guild.id),
                resource,
                amount,
                str(channel_obj.id)
            ))

            db_connection.commit()

            await ctx.send(f"✅ Created recurring order for `{resource}` every `{recurrence}` in {channel_obj.mention} and posted the first one.")

        except Exception as e:
            await ctx.send(f"❌ Failed to create and post order: `{e}`")

# Required setup function
async def setup(bot):
    await bot.add_cog(NewOrder(bot))