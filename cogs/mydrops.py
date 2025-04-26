# cogs/mydrops.py

from discord.ext import commands
from db import cursor

class MyDrops(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def mydrops(self, ctx):
        user_id = str(ctx.author.id)
        server_id = str(ctx.guild.id)

        # Join Dropoffs -> GeneratedOrders to get resource names
        cursor.execute("""
            SELECT go.resource_name, SUM(d.amount)
            FROM Dropoffs d
            JOIN GeneratedOrders go ON d.order_id = go.id
            WHERE d.user_id = %s AND go.server_id = %s
            GROUP BY go.resource_name
            ORDER BY SUM(d.amount) DESC;
        """, (user_id, server_id))

        results = cursor.fetchall()

        if not results:
            await ctx.send(f"📭 {ctx.author.mention}, you haven't dropped anything off yet.")
            return

        message = f"📦 {ctx.author.mention}, you have dropped off:\n"
        for resource, total in results:
            message += f"- `{total}` {resource}\n"

        await ctx.send(message)

async def setup(bot):
    await bot.add_cog(MyDrops(bot))
