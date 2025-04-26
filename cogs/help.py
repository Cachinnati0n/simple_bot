# cogs/help.py

from discord.ext import commands
import discord


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_command(self, ctx):
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            await ctx.send("⚠️ I don't have permission to delete messages.")
        except discord.HTTPException:
            await ctx.send("⚠️ Couldn't delete the message.")
        help_message = (
            "**📘 Foxhole Logistics Bot Help**\n\n"
            "**Order Management**\n"
            "`!neworder <amount> <resource> <recurrence> <#channel>` — Create a recurring order and post the first one\n"
            "`!dropoff <resource> <amount>` — Contribute to a current order (deletes your command message)\n"
            "`!orders` — View all active orders with progress bars\n"
            "`!completedorders` — View recently fulfilled orders\n"
            "`!status` — View all recurring orders with status and next run\n\n"
            "**Control Commands (Admin)**\n"
            "`!pauseorder <order_id>` — Pause a recurring order\n"
            "`!resumeorder <order_id>` — Resume a paused order\n"
            "`!setamount <order_id> <new_amount>` — Change the target amount for a recurring order\n\n"
            "**User Stats**\n"
            "`!mydrops` — View how much you’ve dropped off by resource\n"
            "`!help` — Show this help message\n\n"
            "_Ensure that `recurrence` is one of: `daily`, `weekly`, `every_2_days`, `monthly`_"
        )

        await ctx.send(help_message)

async def setup(bot):
    await bot.add_cog(Help(bot))
