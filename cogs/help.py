import discord
from discord.ext import commands

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_command(self, ctx):
        embed = discord.Embed(
            title="📘 Foxhole Logistics Bot Commands",
            color=discord.Color.dark_blue()
        )

        embed.add_field(
            name="📦 Order Management",
            value=(
                "`!neworder <amount> <resource> <recurrence> <#channel>` — Create a recurring order and post the first instance.\n"
                "`!orders` — View currently active generated orders.\n"
                "`!completedorders` — Show recently fulfilled orders.\n"
                "`!dropoff <resource> <amount>` — Log a resource drop-off manually.\n"
                "`!mydrops` — View your personal drop-off stats by resource."
            ),
            inline=False
        )

        embed.add_field(
            name="🛠 Admin Controls",
            value=(
                "`!pauseorder <order_id>` — Temporarily disable a recurring order.\n"
                "`!resumeorder <order_id>` — Resume a paused recurring order.\n"
                "`!setamount <order_id> <new_amount>` — Change the target quantity of a recurring order.\n"
                "`!deleteorder <order_id>` — Remove a generated order and its drop-off logs.\n"
                "`!postpanel` — Post or refresh the interactive drop-off panel in a channel."
            ),
            inline=False
        )

        embed.add_field(
            name="📊 Status & Info",
            value=(
                "`!status` — Show all recurring orders, their schedule, and progress.\n"
                "`!ping` — Check if the bot is alive.\n"
                "`!help` — Show this help message."
            ),
            inline=False
        )

        embed.add_field(
            name="🧮 Other Commands",
            value=(
                "`!leaderboard` — See who’s contributed the most resources.\n"
                "`!postproduction` — Adds UI buttons to start a new production order."
            ),
            inline=False
        )

        embed.add_field(
            name="🔁 Recurrence Options",
            value="`daily`, `weekly`, `every_2_days`, `monthly`\nUse the order ID from `!status` or the panel when using admin commands.",
            inline=False
        )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(HelpCommand(bot))
