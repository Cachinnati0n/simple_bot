# cogs/completedorders.py

from discord.ext import commands
from db import cursor

class CompletedOrders(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def completedorders(self, ctx, limit: int = 5):
        server_id = str(ctx.guild.id)

        cursor.execute("""
            SELECT resource_name, amount, fulfilled_amount, created_at
            FROM GeneratedOrders
            WHERE server_id = %s AND status = 'complete'
            ORDER BY created_at DESC
            LIMIT %s;
        """, (server_id, limit))

        results = cursor.fetchall()

        if not results:
            await ctx.send("📭 No completed orders yet.")
            return

        message = f"📜 **Most Recent Completed Orders:**\n"
        for resource, amt, fulfilled, timestamp in results:
            message += f"- `{resource}`: {fulfilled}/{amt} ✅ ({timestamp.strftime('%Y-%m-%d')})\n"

        await ctx.send(message)

async def setup(bot):
    await bot.add_cog(CompletedOrders(bot))
