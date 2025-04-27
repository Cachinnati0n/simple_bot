# cogs/dropoff_ui.py

import discord
from discord.ext import commands
from db import cursor, db_connection

class DropoffModal(discord.ui.Modal, title="Submit Dropoff"):

    def __init__(self, active_orders):
        super().__init__()
        self.active_orders = active_orders

        self.order_select = discord.ui.Select(
            placeholder="Select an order...",
            options=[
                discord.SelectOption(label=f"{res} (ID {oid})", value=str(oid))
                for oid, res in active_orders
            ]
        )
        self.add_item(self.order_select)

        self.amount_input = discord.ui.TextInput(
            label="Amount Dropped Off",
            placeholder="e.g. 500",
            required=True
        )
        self.add_item(self.amount_input)

    async def on_submit(self, interaction: discord.Interaction):
        order_id = int(self.order_select.values[0])
        user_id = str(interaction.user.id)
        server_id = str(interaction.guild.id)

        try:
            amount = int(self.amount_input.value)
        except ValueError:
            await interaction.response.send_message("❌ Invalid amount entered.", ephemeral=True)
            return

        # Get order details
        cursor.execute("""
            SELECT amount, fulfilled_amount
            FROM GeneratedOrders
            WHERE id = %s AND server_id = %s;
        """, (order_id, server_id))
        row = cursor.fetchone()

        if not row:
            await interaction.response.send_message("❌ Could not find that order.", ephemeral=True)
            return

        target, fulfilled = row
        new_total = fulfilled + amount

        cursor.execute("""
            INSERT INTO Dropoffs (order_id, user_id, amount)
            VALUES (%s, %s, %s);
        """, (order_id, user_id, amount))

        cursor.execute("""
            UPDATE GeneratedOrders
            SET fulfilled_amount = %s
            WHERE id = %s;
        """, (new_total, order_id))

        if new_total >= target:
            cursor.execute("""
                UPDATE GeneratedOrders
                SET status = 'complete'
                WHERE id = %s;
            """, (order_id,))

        db_connection.commit()

                # Refresh the panel UI
        panel_cog = self.bot.get_cog("DropoffUIPanel")
        if panel_cog:
            await panel_cog.refresh_panel()


        await interaction.response.send_message(
            f"✅ Logged {amount} units to order `{order_id}`.\n📊 Progress: {new_total}/{target} ({new_total/target:.1%})",
            ephemeral=True
        )

class DropoffPanelView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Drop Off", style=discord.ButtonStyle.green, custom_id="dropoff_button")
    async def dropoff_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        server_id = str(interaction.guild.id)
        cursor.execute("""
            SELECT id, resource_name
            FROM GeneratedOrders
            WHERE server_id = %s AND status = 'open'
            ORDER BY created_at DESC;
        """, (server_id,))
        orders = cursor.fetchall()

        if not orders:
            await interaction.response.send_message("📭 No active orders to drop off into.", ephemeral=True)
            return

        modal = DropoffModal(active_orders=orders)
        await interaction.response.send_modal(modal)

class DropoffUIPanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def postpanel(self, ctx):
        """Post the Drop Off button panel to the current channel."""
        view = DropoffPanelView(self.bot)

        # Get all active orders for this server
        server_id = str(ctx.guild.id)
        cursor.execute("""
            SELECT resource_name, amount, fulfilled_amount
            FROM GeneratedOrders
            WHERE server_id = %s AND status = 'open'
            ORDER BY created_at DESC;
        """, (server_id,))
        active_orders = cursor.fetchall()

        if not active_orders:
            await ctx.send("📭 No active orders to display.", view=view)
            return

        # Build the progress text
        msg = "📦 Click below to log your drop-off:\n\n"
        for res, amount, fulfilled in active_orders:
            percent = fulfilled / amount
            bar = self.progress_bar(percent)
            msg += f"✅ `{res}` — {fulfilled}/{amount} ({percent:.1%}) {bar}\n"

        message = await ctx.send(msg, view=view)

        # Store the panel reference on the bot object
        self.bot.panel_message_id = message.id
        self.bot.panel_channel_id = message.channel.id


        await ctx.send(msg, view=view)
    async def refresh_panel(self):
        if not hasattr(self.bot, "panel_message_id") or not hasattr(self.bot, "panel_channel_id"):
            return  # panel hasn't been posted yet

        channel = self.bot.get_channel(self.bot.panel_channel_id)
        if not channel:
            return

        try:
            message = await channel.fetch_message(self.bot.panel_message_id)
        except discord.NotFound:
            return  # message deleted

        # Rebuild the message content
        server_id = str(channel.guild.id)
        cursor.execute("""
            SELECT resource_name, amount, fulfilled_amount
            FROM GeneratedOrders
            WHERE server_id = %s AND status = 'open'
            ORDER BY created_at DESC;
        """, (server_id,))
        active_orders = cursor.fetchall()

        if not active_orders:
            await message.edit(content="📭 No active orders to display.")
            return

        msg = "📦 Click below to log your drop-off:\n\n"
        for res, amount, fulfilled in active_orders:
            percent = fulfilled / amount
            bar = self.progress_bar(percent)
            msg += f"✅ `{res}` — {fulfilled}/{amount} ({percent:.1%}) {bar}\n"

        await message.edit(content=msg)

    def progress_bar(self, percent):
        filled = int(percent * 10)
        return "▰" * filled + "▱" * (10 - filled)


async def setup(bot):
    await bot.add_cog(DropoffUIPanel(bot))
