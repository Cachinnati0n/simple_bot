import discord
from discord.ext import commands
from discord.utils import get
from db import cursor, db_connection

class OneTimeOrder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="orderonce")
    async def orderonce(self, ctx, amount: int, resource: str, *, channel: str):
        """Create a one-time order (not recurring)."""
        channel_obj = get(ctx.guild.text_channels, mention=channel) or \
                      get(ctx.guild.text_channels, name=channel.strip("#"))

        if not channel_obj:
            await ctx.send("❌ Couldn't find that channel.")
            return

        cursor.execute("""
            INSERT INTO GeneratedOrders (
                recurring_order_id, user_id, server_id,
                resource_name, amount, fulfilled_amount, channel_id
            ) VALUES (NULL, %s, %s, %s, %s, 0, %s);
        """, (
            str(ctx.author.id),
            str(ctx.guild.id),
            resource,
            amount,
            str(channel_obj.id)
        ))
        db_connection.commit()

        await channel_obj.send(
            f"📦 **One-Time Order Posted!**\n"
            f"Resource: `{resource}`\n"
            f"Target Amount: `{amount}`\n"
            f"Drop-offs accepted below."
        )

        await ctx.send(f"✅ One-time order for `{resource}` posted in {channel_obj.mention}.")

async def setup(bot):
    await bot.add_cog(OneTimeOrder(bot))
