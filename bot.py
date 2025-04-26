# bot.py
import discord
from discord.ext import commands
import os
from db import cursor, db_connection


intents = discord.Intents.default()
intents.message_content = True  # Needed to read messages

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

@bot.command()
async def testdb(ctx):
    try:
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        if tables:
            await ctx.send(f"✅ Connected! Found {len(tables)} table(s): {[t[0] for t in tables]}")
        else:
            await ctx.send("⚠️ Connected to DB, but no tables found.")
    except Exception as e:
        await ctx.send(f"❌ DB connection failed: `{e}`")

bot.run(os.getenv("DISCORD_TOKEN"))
