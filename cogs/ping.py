# cogs/ping.py

from discord.ext import commands

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        await ctx.send("🏓 Pong!")

# This is required for the cog to be loaded
async def setup(bot):
    await bot.add_cog(Ping(bot))