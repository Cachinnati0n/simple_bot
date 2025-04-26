# bot.py
import discord
from discord.ext import commands
import os
from db import cursor, db_connection
from datetime import datetime
import asyncio


intents = discord.Intents.default()
intents.message_content = True  # Needed to read messages

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

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
            await ctx.send("Attempting to create tables!")
            initialize_tables()
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()
            await ctx.send(f"✅ Connected! Found {len(tables)} table(s): {[t[0] for t in tables]}")
    except Exception as e:
        await ctx.send(f"❌ DB connection failed: `{e}`")

async def load_cogs():
    await bot.load_extension("cogs.neworder")




def initialize_tables():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS RecurringOrders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(50) NOT NULL,
            server_id VARCHAR(50) NOT NULL,
            resource_name VARCHAR(100) NOT NULL,
            amount INT NOT NULL,
            recurrence VARCHAR(50) NOT NULL,
            next_run_time DATETIME NOT NULL,
            channel_id VARCHAR(50) NOT NULL,
            active BOOLEAN DEFAULT TRUE
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS GeneratedOrders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            recurring_order_id INT,
            user_id VARCHAR(50) NOT NULL,
            server_id VARCHAR(50) NOT NULL,
            resource_name VARCHAR(100) NOT NULL,
            amount INT NOT NULL,
            fulfilled_amount INT DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            channel_id VARCHAR(50) NOT NULL,
            FOREIGN KEY (recurring_order_id) REFERENCES RecurringOrders(id)
        );
    """)

    db_connection.commit()





async def main():
    await load_cogs()
    await bot.start(os.getenv("DISCORD_TOKEN"))
asyncio.run(main())