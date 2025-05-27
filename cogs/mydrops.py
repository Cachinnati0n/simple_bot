# cogs/mydrops.py

from discord.ext import commands
from db import cursor
import discord

class MyDrops(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    
    async def mydrops(self, ctx):
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass  # silently fail if it can't delete
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

    @commands.command()
    async def leaderboard(self, ctx):
        server_id = str(ctx.guild.id)
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass  # silently fail if it can't delete
        cursor.execute("""
            SELECT user_id, SUM(amount) as total
            FROM Dropoffs
            JOIN GeneratedOrders ON Dropoffs.order_id = GeneratedOrders.id
            WHERE GeneratedOrders.server_id = %s
            GROUP BY user_id
            ORDER BY total DESC
            LIMIT 10;
        """, (server_id,))
        results = cursor.fetchall()

        if not results:
            await ctx.send("📭 No dropoffs recorded yet.", ephemeral=True)
            return

        leaderboard = "**🏆 Top Contributors:**\n\n"
        for rank, (user_id, total) in enumerate(results, 1):
            member = ctx.guild.get_member(int(user_id)) or await ctx.guild.fetch_member(int(user_id))
            name = member.display_name if member else f"User {user_id}"
            leaderboard += f"**#{rank}** – {name}: `{total}` units\n"

        await ctx.send(leaderboard, ephemeral=True)


async def setup(bot):
    await bot.add_cog(MyDrops(bot))
