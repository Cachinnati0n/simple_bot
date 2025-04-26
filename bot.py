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



async def order_scheduler():
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

            # Get all recurring orders that are due
            cursor.execute("""
                SELECT * FROM RecurringOrders
                WHERE next_run_time <= %s AND active = TRUE;
            """, (now,))
            due_orders = cursor.fetchall()

            for order in due_orders:
                id, user_id, server_id, resource_name, amount, recurrence, next_run, channel_id, active = order

                # Post the new order in the assigned channel
                guild = bot.get_guild(int(server_id))
                channel = guild.get_channel(int(channel_id))

                if not channel:
                    print(f"⚠️ Could not find channel ID {channel_id}")
                    continue

                await channel.send(
                    f"📦 **New Order Posted!**\n"
                    f"Resource: `{resource_name}`\n"
                    f"Target Amount: `{amount}`\n"
                    f"Drop-offs accepted below."
                )

                # Add to GeneratedOrders
                cursor.execute("""
                    INSERT INTO GeneratedOrders (
                        recurring_order_id, user_id, server_id, resource_name,
                        amount, fulfilled_amount, channel_id
                    ) VALUES (%s, %s, %s, %s, %s, 0, %s);
                """, (
                    id, user_id, server_id, resource_name, amount, channel_id
                ))

                # Calculate new next_run_time
                new_next = calculate_next_run(recurrence).strftime('%Y-%m-%d %H:%M:%S')

                # Update RecurringOrders
                cursor.execute("""
                    UPDATE RecurringOrders SET next_run_time = %s WHERE id = %s;
                """, (new_next, id))

                db_connection.commit()

        except Exception as e:
            print(f"❌ Scheduler error: {e}")

        await asyncio.sleep(60)  # Check every 60 seconds


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
    bot.loop.create_task(order_scheduler()) #runs the check for spawning a new task
    await bot.start(os.getenv("DISCORD_TOKEN"))

asyncio.run(main())
