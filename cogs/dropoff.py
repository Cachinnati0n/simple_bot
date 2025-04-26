# cogs/dropoff.py

import discord
from discord.ext import commands
from db import cursor, db_connection
from datetime import datetime

class Dropoff(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def dropoff(self, ctx, resource: str, amount: int):
        server_id = str(ctx.guild.id)

        # Find the most recent unfulfilled order
        cursor.execute("""
            SELECT id, amount, fulfilled_amount FROM GeneratedOrders
            WHERE server_id = %s AND resource_name = %s
            ORDER BY created_at DESC
            LIMIT 1;
        """, (server_id, resource))
        order = cursor.fetchone()

        if not order:
            await ctx.send(f"⚠️ No active order found for `{resource}`.")
            return

        order_id, target_amount, current_fulfilled = order
        new_fulfilled = current_fulfilled + amount

        # Insert the dropoff
        cursor.execute("""
            INSERT INTO Dropoffs (order_id, user_id, amount)
            VALUES (%s, %s, %s);
        """, (order_id, str(ctx.author.id), amount))

        # Update order's fulfilled amount
        cursor.execute("""
            UPDATE GeneratedOrders
            SET fulfilled_amount = %s
            WHERE id = %s;
        """, (new_fulfilled, order_id))

        db_connection.commit()

        percent = (new_fulfilled / target_amount) * 100
        await ctx.send(
            f"✅ {ctx.author.mention} dropped {amount} `{resource}`\n"
            f"📊 Order progress: {new_fulfilled} / {target_amount} ({percent:.1f}%)"
        )

# Required setup
async def setup(bot):
    await bot.add_cog(Dropoff(bot))
