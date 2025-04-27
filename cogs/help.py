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
            pass  # silently fail if it can't delete

        help_text = (
            "**📘 Foxhole Logistics Bot Commands**\n\n"

            "**📦 Order Management**\n"
            "`!neworder <amount> <resource> <recurrence> <#channel>` — Create a recurring order and post the first instance.\n"
            "`!orders` — View currently active generated orders.\n"
            "`!completedorders` — Show recently fulfilled orders.\n"
            "`!dropoff <resource> <amount>` — Log a resource drop-off manually.\n"
            "`!mydrops` — View your personal drop-off stats by resource.\n\n"

            "**🛠 Admin Controls**\n"
            "`!pauseorder <order_id>` — Temporarily disable a recurring order.\n"
            "`!resumeorder <order_id>` — Resume a paused recurring order.\n"
            "`!setamount <order_id> <new_amount>` — Change the target quantity of a recurring order.\n"
            "`!deleteorder <order_id>` — Remove a generated order and its drop-off logs.\n"
            "`!postpanel` — Post or refresh the interactive drop-off panel in a channel.\n\n"

            "**📊 Status & Info**\n"
            "`!status` — Show all recurring orders, their schedule, and progress.\n"
            "`!ping` — Check if the bot is alive.\n"
            "`!help` — Show this help message.\n\n"

            "**🔁 Recurrence Options:** `daily`, `weekly`, `every_2_days`, `monthly`\n"
            "Use the `order ID` from `!status` or the panel when using admin commands.\n"
        )

        await ctx.send(help_text)

async def setup(bot):
    await bot.add_cog(Help(bot))
