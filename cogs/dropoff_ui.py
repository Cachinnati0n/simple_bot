import discord
from discord.ext import commands
import asyncio
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
        modal = DropoffModal()
        await interaction.response.send_modal(modal)


class DropoffUIPanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Panel cache: { server_id: (channel_id, message_id) }
        self.bot.panel_channel_id_map = {}
        self.bot.panel_message_id_map = {}

        # Load existing panels from DB
        cursor.execute("SELECT server_id, channel_id, message_id FROM DropoffPanel")
        for server_id, channel_id, message_id in cursor.fetchall():
            self.bot.panel_channel_id_map[server_id] = int(channel_id)
            self.bot.panel_message_id_map[server_id] = int(message_id)

        self.bg_task = bot.loop.create_task(self.auto_refresh_panel())

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def postpanel(self, ctx):
        """Post the Drop Off button panel to the current channel."""
        view = DropoffPanelView(self.bot)
        server_id = str(ctx.guild.id)

        cursor.execute("""
            SELECT id, resource_name, amount, fulfilled_amount
            FROM GeneratedOrders
            WHERE server_id = %s AND status = 'open'
            ORDER BY created_at DESC;
        """, (server_id,))
        active_orders = cursor.fetchall()

        if not active_orders:
            message = await ctx.send("📭 No active orders to display.", view=view)
            self.bot.panel_channel_id_map[server_id] = message.channel.id
            self.bot.panel_message_id_map[server_id] = message.id
            await ctx.message.delete()
            return

        msg = "📦 Click below to log your drop-off:\n\n"
        for order_id, res, amount, fulfilled in active_orders:
            percent = fulfilled / amount
            bar = self.progress_bar(percent)
            msg += f"✅ [`{order_id}`] `{res}` — {fulfilled}/{amount} ({percent:.1%}) {bar}\n"

        message = await ctx.send(msg, view=view)

        # Save panel reference
        self.bot.panel_channel_id_map[server_id] = message.channel.id
        self.bot.panel_message_id_map[server_id] = message.id

        cursor.execute("""
            INSERT INTO DropoffPanel (server_id, channel_id, message_id)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE channel_id = VALUES(channel_id), message_id = VALUES(message_id);
        """, (server_id, str(message.channel.id), str(message.id)))
        db_connection.commit()

        await ctx.message.delete()

    async def refresh_panel(self):
        for server_id, channel_id in list(self.bot.panel_channel_id_map.items()):
            try:
                message_id = self.bot.panel_message_id_map.get(server_id)
                if not message_id:
                    continue

                guild = self.bot.get_guild(int(server_id))
                if not guild:
                    continue

                channel = guild.get_channel(int(channel_id))
                if not channel:
                    continue

                try:
                    message = await channel.fetch_message(int(message_id))
                except discord.NotFound:
                    # Clean up orphaned entry
                    del self.bot.panel_channel_id_map[server_id]
                    del self.bot.panel_message_id_map[server_id]
                    cursor.execute("DELETE FROM DropoffPanel WHERE server_id = %s", (server_id,))
                    db_connection.commit()
                    continue

                cursor.execute("""
                    SELECT id, resource_name, amount, fulfilled_amount
                    FROM GeneratedOrders
                    WHERE server_id = %s AND status = 'open'
                    ORDER BY created_at DESC;
                """, (server_id,))
                active_orders = cursor.fetchall()

                view = DropoffPanelView(self.bot)

                if not active_orders:
                    await message.edit(content="📭 No active orders to display.", view=view)
                    continue

                msg = "📦 Click below to log your drop-off:\n\n"
                for order_id, res, amount, fulfilled in active_orders:
                    percent = fulfilled / amount
                    bar = self.progress_bar(percent)
                    msg += f"✅ [`{order_id}`] `{res}` — {fulfilled}/{amount} ({percent:.1%}) {bar}\n"

                await message.edit(content=msg, view=view)

            except Exception as e:
                print(f"⚠️ Failed to refresh panel for server {server_id}: {e}")

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
