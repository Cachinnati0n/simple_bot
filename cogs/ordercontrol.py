# cogs/ordercontrol.py

from discord.ext import commands
from db import cursor, db_connection
import discord

class OrderControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def pauseorder(self, ctx, order_id: int):
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                await ctx.send("⚠️ I don't have permission to delete messages.")
            except discord.HTTPException:
                await ctx.send("⚠️ Couldn't delete the message.")

            cursor.execute("""
                UPDATE RecurringOrders
                SET active = FALSE
                WHERE id = %s AND server_id = %s AND active = TRUE;
                """, (order_id, str(ctx.guild.id)))
            db_connection.commit()

            if cursor.rowcount:
                await ctx.send(f"⏸️ Recurring order ID `{order_id}` has been paused.")
            else:
                await ctx.send(f"⚠️ No active recurring order with ID `{order_id}` found.")


    @commands.command()
    async def resumeorder(self, ctx, order_id: int):
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            await ctx.send("⚠️ I don't have permission to delete messages.")
        except discord.HTTPException:
            await ctx.send("⚠️ Couldn't delete the message.")

        cursor.execute("""
            UPDATE RecurringOrders
            SET active = TRUE
            WHERE id = %s AND server_id = %s AND active = FALSE;
        """, (order_id, str(ctx.guild.id)))
        db_connection.commit()

        if cursor.rowcount:
            await ctx.send(f"▶️ Recurring order ID `{order_id}` has been resumed.")
        else:
            await ctx.send(f"⚠️ No paused recurring order with ID `{order_id}` found.")


    
    @commands.command()
    async def setamount(self, ctx, order_id: int, new_amount: int):
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            await ctx.send("⚠️ I don't have permission to delete messages.")
        except discord.HTTPException:
            await ctx.send("⚠️ Couldn't delete the message.")
        cursor.execute("""
            UPDATE RecurringOrders
            SET amount = %s
            WHERE id = %s AND server_id = %s;
        """, (new_amount, order_id, str(ctx.guild.id)))
        db_connection.commit()

        if cursor.rowcount:
            await ctx.send(f"✏️ Updated recurring order ID `{order_id}` to `{new_amount}` units.")
        else:
            await ctx.send(f"⚠️ No recurring order with ID `{order_id}` found.")


async def setup(bot):
    await bot.add_cog(OrderControl(bot))
