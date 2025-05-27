import discord
from discord.ext import commands
import asyncio
from db import cursor, db_connection
from cogs import productionthreadpanel

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

        # Refresh full dropoff panel
        panel_cog = interaction.client.get_cog("DropoffUIPanel")
        if panel_cog:
            await panel_cog.refresh_panel()

        # Refresh thread mini-panel if tied to a production order
        cursor.execute("SELECT production_order_id FROM GeneratedOrders WHERE id = %s;", (order_id,))
        prod_row = cursor.fetchone()

        if prod_row and prod_row[0] is not None:
            production_order_id = prod_row[0]
            prod_cog = interaction.client.get_cog("ProductionThreadPanel")
            if prod_cog:
                await prod_cog.refresh_panel(production_order_id)

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
        modal = DropoffModal()
        await interaction.response.send_modal(modal)


class DropoffUIPanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Load panel data from DB
        cursor.execute("SELECT server_id, channel_id, message_id FROM DropoffPanel")
        for server_id, channel_id, message_id in cursor.fetchall():
            self.bot.panel_channel_id = int(channel_id)
            self.bot.panel_message_id = int(message_id)

        self.bg_task = bot.loop.create_task(self.auto_refresh_panel())

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def postpanel(self, ctx):
        """Post the Drop Off button panel to the current channel."""
        view = DropoffPanelView(self.bot)

        server_id = str(ctx.guild.id)
        cursor.execute("""
            SELECT id, resource_name, amount, fulfilled_amount, production_order_id
            FROM GeneratedOrders
            WHERE server_id = %s AND status = 'open'
            ORDER BY created_at DESC;
        """, (server_id,))
        active_orders = cursor.fetchall()

        if not active_orders:
            message = await ctx.send("📭 No active orders to display.", view=view)
            self.bot.panel_message_id = message.id
            self.bot.panel_channel_id = message.channel.id
            await ctx.message.delete()
            return

        msg = self.build_grouped_panel(active_orders)

        message = await ctx.send(msg, view=view)
        self.bot.panel_message_id = message.id
        self.bot.panel_channel_id = message.channel.id
        await ctx.message.delete()

        cursor.execute("""
            INSERT INTO DropoffPanel (server_id, channel_id, message_id)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE channel_id = VALUES(channel_id), message_id = VALUES(message_id);
        """, (server_id, str(message.channel.id), str(message.id)))
        db_connection.commit()

    async def refresh_panel(self):
        if not hasattr(self.bot, "panel_message_id") or not hasattr(self.bot, "panel_channel_id"):
            print("[DropoffUIPanel] Panel message or channel not set.")
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
            SELECT id, resource_name, amount, fulfilled_amount, production_order_id
            FROM GeneratedOrders
            WHERE server_id = %s AND status = 'open'
            ORDER BY created_at DESC;
        """, (server_id,))
        active_orders = cursor.fetchall()

        view = DropoffPanelView(self.bot)

        if not active_orders:
            await message.edit(content="📭 No active orders to display.", view=view)
            return

        msg = self.build_grouped_panel(active_orders)
        await message.edit(content=msg, view=view)

    def build_grouped_panel(self, active_orders):
        from collections import defaultdict

        grouped = defaultdict(list)
        for row in active_orders:
            grouped[row[4]].append(row)  # group by production_order_id (can be None)

        msg = "📦 Click below to log your drop-off:\n\n"

        for prod_id, orders in grouped.items():
            if prod_id:
                cursor.execute("SELECT title FROM ProductionOrders WHERE id = %s", (prod_id,))
                result = cursor.fetchone()
                title = result[0] if result else f"Production {prod_id}"
                msg += f"🛠️ **{title}**\n"
            else:
                msg += "📦 **Independent Orders**\n"

            for order_id, res, amount, fulfilled, _ in orders:
                percent = fulfilled / amount
                bar = self.progress_bar(percent)
                msg += f"✅ [`{order_id}`] `{res}` — {fulfilled}/{amount} ({percent:.1%}) {bar}\n"

            msg += "\n"
        return msg

    async def auto_refresh_panel(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await asyncio.sleep(120)  # every 2 minutes
            await self.refresh_panel()

    def progress_bar(self, percent):
        filled = int(percent * 10)
        return "▰" * filled + "▱" * (10 - filled)


async def setup(bot):
    await bot.add_cog(DropoffUIPanel(bot))
