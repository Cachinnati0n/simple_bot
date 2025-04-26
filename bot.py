# bot.py
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True  # Needed to read messages

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

import os
bot.run(os.getenv("DISCORD_TOKEN"))
