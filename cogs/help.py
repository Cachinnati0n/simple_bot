import discord
from discord.ext import commands

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_command(self, ctx):
        embed = discord.Embed(
            title="🛠️ Dash Logistics Bot Help",
            description="Here are the available commands:",
            color=discord.Color.green()
        )

        embed.add_field(
            name="`!neworder`",
            value="Create a recurring resource order with automatic posting.",
            inline=False
        )

        embed.add_field(
            name="`!orderonce`",
            value="Create a one-time resource order.",
            inline=False
        )

        embed.add_field(
            name="`!dropoff`",
            value="Log a resource drop-off manually (or use button panels).",
            inline=False
        )

        embed.add_field(
            name="`!mydrops`",
            value="Check your personal drop-off contribution history.",
            inline=False
        )

        embed.add_field(
            name="`!completedorders`",
            value="View recently fulfilled orders.",
            inline=False
        )

        embed.add_field(
            name="`!postproduction`",
            value="(Admin) Post production order UI for creating assembly orders.",
            inline=False
        )

        embed.add_field(
            name="`!orderstatus`",
            value="View all active orders, grouped by production order if relevant.",
            inline=False
        )

        embed.add_field(
            name="`!setchannel`",
            value="(Optional) Set a default channel for order posting.",
            inline=False
        )

        embed.set_footer(text="You can also interact with buttons directly on posted order panels.")

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(HelpCommand(bot))

