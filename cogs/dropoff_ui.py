import discord
from discord.ext import commands
from db import cursor, db_connection

class DropoffModal(discord.ui.Modal, title="Submit Dropoff"):
    def __init__(self):
        super().__init__()

        self.order_input = discord.ui.TextInput(
            label="Order ID",
            placeholder="e.g. 12",
            required=True
        )
        self.add_item(self.order_input)

        self.amount_input = discord.ui.TextInput(
            label="Amount Dropped Off",
            placeholder="e.g. 500",
            required=True
        )
        self.add_item(self.amount_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            order_id = int(self.order_input.value)
            amount = int(self.amount_input.value)
        except ValueError:
            await interaction.response.send_message("❌ Invalid input. Please enter numbers only.", ephemeral=True)
            return

        user_id = str(interaction.user.id)
        server_id = str(interaction.guild.id)

        cursor.execute("""
            SELECT amount, fulfilled_amount FROM GeneratedOrders
            WHERE id = %s AND server_id = %s AND status = 'open';
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
            UPDATE GeneratedOrders SET fulfilled_amount = %s WHERE id = %s;
        """, (new_total, order_id))

        if new_total >= target:
            cursor.execute("""
                UPDATE GeneratedOrders SET status = 'complete' WHERE id = %s;
            """, (order_id,))

        db_connection.commit()

        panel_cog = interaction.client.get_cog("DropoffUIPanel")
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

        modal = DropoffModal()
        await interaction.response.send_modal(modal)


class DropoffUIPanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def postpanel(self, ctx):
        """Post the Drop Off button panel to the current channel."""
        view = DropoffPanelView(self.bot)

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

        msg = "📦 Click below to log your drop-off:\n\n"
        for res, amount, fulfilled in active_orders:
            order_id = self.get_order_id_by_row(server_id, res, amount, fulfilled)
            percent = fulfilled / amount
            bar = self.progress_bar(percent)
            msg += f"✅ [`{order_id}`] `{res}` — {fulfilled}/{amount} ({percent:.1%}) {bar}\n"

        message = await ctx.send(msg, view=view)
        self.bot.panel_message_id = message.id
        self.bot.panel_channel_id = message.channel.id

    async def refresh_panel(self):
        if not hasattr(self.bot, "panel_message_id") or not hasattr(self.bot, "panel_channel_id"):
            return

        channel = self.bot.get_channel(self.bot.panel_channel_id)
        if not channel:
            return

        try:
            message = await channel.fetch_message(self.bot.panel_message_id)
        except discord.NotFound:
            return

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
            order_id = self.get_order_id_by_row(server_id, res, amount, fulfilled)
            percent = fulfilled / amount
            bar = self.progress_bar(percent)
            msg += f"✅ [`{order_id}`] `{res}` — {fulfilled}/{amount} ({percent:.1%}) {bar}\n"

        await message.edit(content=msg)

    def get_order_id_by_row(self, server_id, resource_name, amount, fulfilled):
        cursor.execute("""
            SELECT id FROM GeneratedOrders
            WHERE server_id = %s AND resource_name = %s AND amount = %s AND fulfilled_amount = %s
            ORDER BY created_at DESC LIMIT 1;
        """, (server_id, resource_name, amount, fulfilled))
        row = cursor.fetchone()
        return row[0] if row else "?"

    def progress_bar(self, percent):
        filled = int(percent * 10)
        return "▰" * filled + "▱" * (10 - filled)


async def setup(bot):
    await bot.add_cog(DropoffUIPanel(bot))
