import discord
from discord.ext import commands

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_command(self, ctx):
        embed = discord.Embed(
            title="🛠️ Scrapbook Logistics Help Menu",
            description="Here’s a list of commands and how to use them:",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="`!help`",
            value="Show this help message.",
            inline=False
        )

        embed.add_field(
            name="`!neworder`",
            value="Start a recurring resource order.\n**Syntax:** `!neworder` and follow prompts.",
            inline=False
        )

        embed.add_field(
            name="`!orderonce`",
            value="Create a one-time resource order.\n**Syntax:** `!orderonce` and follow prompts.",
            inline=False
        )

        embed.add_field(
            name="`!postpanel`",
            value="(Admin) Post the full drop-off dashboard.\n**Syntax:** `!postpanel`",
            inline=False
        )

        embed.add_field(
            name="`!postproduction`",
            value="(Admin) Post the UI for starting a production order.\n**Syntax:** `!postproduction`",
            inline=False
        )

        embed.add_field(
            name="`!pauseorder <order_id>`",
            value="(Admin) Pause an active recurring order.\n**Syntax:** `!pauseorder 17`",
            inline=False
        )

        embed.add_field(
            name="`!mydrops`",
            value="List your drop-offs and contributions.\n**Syntax:** `!mydrops`",
            inline=False
        )

        embed.add_field(
            name="`!completedorders`",
            value="View a summary of fulfilled orders.\n**Syntax:** `!completedorders`",
            inline=False
        )

        embed.add_field(
            name="`!status`",
            value="Show current server status and active logistics.\n**Syntax:** `!status`",
            inline=False
        )

        embed.set_footer(text="You can also use interactive buttons in each panel to log drop-offs or create new orders.")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(HelpCommand(bot))
