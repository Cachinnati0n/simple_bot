import discord
from discord.ext import commands
from db import cursor, db_connection
import asyncio
from .productionthreadpanel import post_production_panel

# Recipes
RECIPES = {
    "Flood Mk. 1": {
        "Coke": 49500,
        "Components": 10000,
        "Sulfur": 10000,
        "Salvage for Cmats": 15000
    },
    "Stain": {
        "Coke": 123750,
        "Components": 23000,
        "Sulfur": 26000,
        "Salvage for Cmats": 33000
    }
}

class ProductionOrderModal(discord.ui.Modal):
    def __init__(self, bot, recipe_name):
        super().__init__(title=f"New Production Order: {recipe_name}")
        self.bot = bot
        self.recipe_name = recipe_name

        self.bay_input = discord.ui.TextInput(
            label="Assembly Bay Number",
            placeholder="e.g. 13",
            required=True
        )
        self.add_item(self.bay_input)

        self.name_input = discord.ui.TextInput(
            label="Production Order Name",
            placeholder="e.g. Flood for Armor Group",
            required=True
        )
        self.add_item(self.name_input)

        self.desc_input = discord.ui.TextInput(
            label="Description",
            placeholder="Who it's for, notes, etc.",
            style=discord.TextStyle.paragraph,
            required=False
        )
        self.add_item(self.desc_input)

        self.role_input = discord.ui.TextInput(
            label="Visible to Role (without @)",
            placeholder="e.g. Armor or Logistics",
            required=False
        )
        self.add_item(self.role_input)

    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        server_id = str(interaction.guild.id)
        channel = interaction.channel
        recipe = RECIPES[self.recipe_name]

        # Insert production order
        cursor.execute("""
            INSERT INTO ProductionOrders (server_id, user_id, recipe_name, bay_number, title, description)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            server_id,
            user_id,
            self.recipe_name,
            self.bay_input.value,
            self.name_input.value,
            self.desc_input.value
        ))
        db_connection.commit()

        cursor.execute("SELECT LAST_INSERT_ID();")
        (production_id,) = cursor.fetchone()

        # Generate material orders
        for resource, amount in recipe.items():
            cursor.execute("""
                INSERT INTO GeneratedOrders (
                    production_order_id, server_id, user_id, resource_name, amount, fulfilled_amount, channel_id, status
                ) VALUES (%s, %s, %s, %s, %s, 0, %s, 'open');
            """, (
                production_id,
                server_id,
                user_id,
                resource,
                amount,
                str(channel.id)
            ))
        db_connection.commit()

        # Create thread
        thread = await channel.create_thread(
            name=self.name_input.value,
            type=discord.ChannelType.public_thread
        )

        # Find and add role
        role_name = self.role_input.value.strip()
        role = discord.utils.find(lambda r: r.name.lower() == role_name.lower(), interaction.guild.roles)
        if role:
            await thread.send(f"🔔 {role.mention} - New production order: **{self.name_input.value}**")

        # Send initial panel message (placeholder for now)
        message = await thread.send("📦 Production order dropoff panel will appear here...")

        # Cache panel to DB
        cursor.execute("""
            INSERT INTO ProductionPanels (production_order_id, thread_id, message_id)
            VALUES (%s, %s, %s)
        """, (production_id, str(thread.id), str(message.id)))
        db_connection.commit()

        await interaction.response.send_message(f"✅ Production order **{self.name_input.value}** created in thread {thread.mention}", ephemeral=True)

        # Inside on_submit, after thread is created and message sent:
        await post_production_panel(self.bot, thread, production_id)


class ProductionPanelView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        for recipe_name in RECIPES.keys():
            self.add_item(ProductionRecipeButton(bot, recipe_name))

    @classmethod
    def is_persistent(cls) -> bool:
        return True


class ProductionRecipeButton(discord.ui.Button):
    def __init__(self, bot, recipe_name):
        super().__init__(
            label=recipe_name,
            style=discord.ButtonStyle.blurple,
            custom_id=f"recipe_{recipe_name.replace(' ', '_').lower()}"  # Make it lowercase + underscore-safe
        )
        self.bot = bot
        self.recipe_name = recipe_name

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ProductionOrderModal(self.bot, self.recipe_name))



class ProductionOrders(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def postproduction(self, ctx):
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass  # silently fail if it can't delete

        view = ProductionPanelView(self.bot)
        message = await ctx.send("🛠️ **Start a Production Order:**", view=view)

        # Cache it to the database
        cursor.execute("""
            INSERT INTO ProductionUI (server_id, channel_id, message_id)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE channel_id = VALUES(channel_id), message_id = VALUES(message_id)
        """, (str(ctx.guild.id), str(message.channel.id), str(message.id)))
        db_connection.commit()


async def setup(bot):
    await bot.add_cog(ProductionOrders(bot))