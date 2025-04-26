# cogs/status.py

from discord.ext import commands
from db import cursor
from datetime import datetime
import discord

class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def status(self, ctx):
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            await ctx.send("⚠️ I need permission to delete messages.")
        except discord.HTTPException:
            pass  # silently fail if message is already gone or can't be deleted

        server_id = str(ctx.guild.id)

        cursor.execute("""
            SELECT resource_name, amount, recurrence, next_run_time, active
            FROM RecurringOrders
            WHERE server_id = %s
            ORDER BY next_run_time ASC;
        """, (server_id,))
        results = cursor.fetchall()

        if not results:
            await ctx.send("📭 No recurring orders found.")
            return

        message = "**📋 Recurring Order Status:**\n"
        for resource, amount, recurrence, next_run, active in results:
            icon = "✅" if active else "⏸️"
            next_run_str = next_run.strftime('%Y-%m-%d %H:%M')
            message += f"{icon} `{resource}` — {amount} units — {recurrence} — next at `{next_run_str}`\n"

        await ctx.send(message)

async def setup(bot):
    await bot.add_cog(Status(bot))

