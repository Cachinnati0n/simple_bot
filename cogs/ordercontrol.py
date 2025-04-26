# cogs/ordercontrol.py

from discord.ext import commands
from db import cursor, db_connection

class OrderControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def pauseorder(self, ctx, resource: str):
        server_id = str(ctx.guild.id)

        cursor.execute("""
            UPDATE RecurringOrders
            SET active = FALSE
            WHERE server_id = %s AND resource_name = %s AND active = TRUE
            ORDER BY id DESC
            LIMIT 1;
        """, (server_id, resource))

        db_connection.commit()

        if cursor.rowcount:
            await ctx.send(f"⏸️ Recurring order for `{resource}` has been paused.")
        else:
            await ctx.send(f"⚠️ No active recurring order for `{resource}` found.")

    @commands.command()
    async def resumeorder(self, ctx, resource: str):
        server_id = str(ctx.guild.id)

        cursor.execute("""
            UPDATE RecurringOrders
            SET active = TRUE
            WHERE server_id = %s AND resource_name = %s AND active = FALSE
            ORDER BY id DESC
            LIMIT 1;
        """, (server_id, resource))

        db_connection.commit()

        if cursor.rowcount:
            await ctx.send(f"▶️ Recurring order for `{resource}` has been resumed.")
        else:
            await ctx.send(f"⚠️ No paused recurring order for `{resource}` found.")

async def setup(bot):
    await bot.add_cog(OrderControl(bot))
