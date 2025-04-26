# cogs/orders.py

from discord.ext import commands
from db import cursor
import discord

class Orders(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def orders(self, ctx):
        server_id = str(ctx.guild.id)

        cursor.execute("""
            SELECT resource_name, amount, fulfilled_amount
            FROM GeneratedOrders
            WHERE server_id = %s AND fulfilled_amount < amount
            ORDER BY created_at DESC;
        """, (server_id,))
        open_orders = cursor.fetchall()

        if not open_orders:
            await ctx.send("📭 No active orders at the moment.")
            return

        response = "📦 **Orders in Progress:**\n"
        for resource, amount, fulfilled in open_orders:
            percent = (fulfilled / amount) * 100
            bar = self.progress_bar(percent)
            response += f"- `{resource}`: {fulfilled}/{amount} ({percent:.1f}%) {bar}\n"

        await ctx.send(response)

    def progress_bar(self, percent):
        filled = int(percent // 10)
        return "▰" * filled + "▱" * (10 - filled)

async def setup(bot):
    await bot.add_cog(Orders(bot))
