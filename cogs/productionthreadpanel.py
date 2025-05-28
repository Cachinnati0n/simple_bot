import discord
from db import cursor, db_connection


class ProductionDropoffModal(discord.ui.Modal, title="Submit Dropoff"):

    def __init__(self, production_order_id):
        super().__init__()
        self.production_order_id = production_order_id

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
            WHERE id = %s AND server_id = %s AND production_order_id = %s AND status = 'open';
        """, (order_id, server_id, self.production_order_id))
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

        refresher = interaction.client.get_cog("ProductionPanelRefresher")
        if refresher:
            await refresher.refresh_single_panel(self.production_order_id)

        await interaction.response.send_message(
            f"✅ Logged {amount} units to order `{order_id}`.\n📊 Progress: {new_total}/{target} ({new_total/target:.1%})",
            ephemeral=True
        )


class ProductionDropoffPanelView(discord.ui.View):
    def __init__(self, production_order_id):
        super().__init__(timeout=None)
        self.production_order_id = production_order_id

    @discord.ui.button(label="Drop Off", style=discord.ButtonStyle.green, custom_id="dropoff_button")
    async def dropoff_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ProductionDropoffModal(self.production_order_id))


async def post_production_panel(bot, thread: discord.Thread, production_order_id: int):
    # Get metadata for the production order
    cursor.execute("""
        SELECT description, bay_number FROM ProductionOrders
        WHERE id = %s
    """, (production_order_id,))
    prod_meta = cursor.fetchone()

    description = prod_meta[0] if prod_meta else "No description provided."
    bay_number = prod_meta[1] if prod_meta else "Unknown"

    # Get active orders
    cursor.execute("""
        SELECT id, resource_name, amount, fulfilled_amount
        FROM GeneratedOrders
        WHERE production_order_id = %s AND status = 'open'
        ORDER BY created_at DESC;
    """, (production_order_id,))
    active_orders = cursor.fetchall()

    if not active_orders:
        await thread.send("📭 No active orders for this production.")
        return

    # Build message
    msg = f"📦 **Production Order Drop-Off Panel**\n"
    msg += f"🏭 **Assembly Bay:** `{bay_number}`\n"
    msg += f"📝 **Description:** {description}\n\n"

    for order_id, res, amount, fulfilled in active_orders:
        percent = fulfilled / amount
        bar = "▰" * int(percent * 10) + "▱" * (10 - int(percent * 10))
        msg += f"✅ [`{order_id}`] `{res}` — {fulfilled}/{amount} ({percent:.1%}) {bar}\n"

    view = ProductionDropoffPanelView(production_order_id)
    message = await thread.send(content=msg, view=view)

    # Cache the message and thread
    cursor.execute("""
        INSERT INTO ProductionPanels (production_order_id, thread_id, message_id)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE thread_id = VALUES(thread_id), message_id = VALUES(message_id);
    """, (production_order_id, str(thread.id), str(message.id)))
    db_connection.commit()


async def refresh_panel(bot, production_order_id: int):
    # Get the panel message info
    cursor.execute("""
        SELECT thread_id, message_id FROM ProductionPanels
        WHERE production_order_id = %s;
    """, (production_order_id,))
    row = cursor.fetchone()

    if not row:
        return

    thread_id, message_id = int(row[0]), int(row[1])
    thread = bot.get_channel(thread_id)
    if not thread:
        return

    try:
        message = await thread.fetch_message(message_id)
    except discord.NotFound:
        return

    # Get the active orders
    cursor.execute("""
        SELECT id, resource_name, amount, fulfilled_amount
        FROM GeneratedOrders
        WHERE production_order_id = %s AND status = 'open'
        ORDER BY created_at DESC;
    """, (production_order_id,))
    active_orders = cursor.fetchall()

    if not active_orders:
        await message.edit(content="📭 No active orders for this production.", view=None)
        try:
            await thread.edit(archived=True)
        except discord.Forbidden:
            print(f"[refresh_panel] Failed to archive thread {thread_id}: insufficient permissions.")
        return

    # If still active orders, update the panel
    msg = "📦 Production Order Drop-Off Panel:\n\n"
    for order_id, res, amount, fulfilled in active_orders:
        percent = fulfilled / amount
        bar = "▰" * int(percent * 10) + "▱" * (10 - int(percent * 10))
        msg += f"✅ [`{order_id}`] `{res}` — {fulfilled}/{amount} ({percent:.1%}) {bar}\n"

    view = ProductionDropoffPanelView(production_order_id)
    await message.edit(content=msg, view=view)
