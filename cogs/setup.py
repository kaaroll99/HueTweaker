import logging
import re
from datetime import datetime, timedelta

import discord
from discord import app_commands, Embed
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput, Select

from bot import db, cmd_messages
from database import model
from utils.color_format import ColorUtils
from utils.data_loader import load_json


# GŁÓWNY widok z przyciskami
class SetupEmbedView(discord.ui.View):
    def __init__(self, colors_data: dict, guild_id: int):
        super().__init__(timeout=180)
        self.guild_id = guild_id
        self.colors_data = colors_data or {}

        if not any(self.colors_data.values()):
            create_button = Button(label="CREATE", style=discord.ButtonStyle.primary, custom_id="create_button")
            create_button.callback = self.create_callback
            self.add_item(create_button)
        else:
            add_button = Button(label="ADD", style=discord.ButtonStyle.success, custom_id="add_color")
            add_button.callback = self.add_color_callback
            self.add_item(add_button)
            
            edit_button = Button(label="EDIT", style=discord.ButtonStyle.secondary, custom_id="edit_color")
            edit_button.callback = self.edit_color_callback
            self.add_item(edit_button)
        
        # back_button = Button(label="BACK", style=discord.ButtonStyle.danger, custom_id="back_main")
        # back_button.callback = self.back_callback
        # self.add_item(back_button)

    async def create_callback(self, interaction: discord.Interaction):
        try:
            with db as session:
                query = session.create(model.select_class("select"), {"server_id": interaction.guild.id})
            
            if query:
                with db as session:
                    query_result = session.select(model.select_class("select"), {"server_id": interaction.guild.id})
                new_colors = query_result[0] if query_result else {}
                
                new_embed = discord.Embed(
                    title="Konfiguracja kolorów",
                    description="Utworzono listę. Możesz teraz modyfikować kolory.",
                    color=4539717
                )
                
                new_view = SetupEmbedView(new_colors, interaction.guild.id)
                await interaction.response.send_message(embed=new_embed, view=new_view, ephemeral=True)
            else:
                await interaction.response.send_message("Błąd przy tworzeniu listy", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Wystąpił błąd: {str(e)}", ephemeral=True)


    async def add_color_callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("ADD button works!", ephemeral=True)


    async def edit_color_callback(self, interaction: discord.Interaction):
        try:
            # Tworzymy listę kolorów, które są już ustawione
            with db as session:
                query_result = session.select(model.select_class("select"), {"server_id": interaction.guild.id})
            
            if not query_result:
                await interaction.response.send_message("Brak kolorów do edycji.", ephemeral=True)
                return
                
            colors_data = query_result[0]
            available_colors = []
            
            # Zbieramy wszystkie ustawione kolory
            for i in range(1, 11):
                color_key = f"hex_{i}"
                if colors_data.get(color_key):
                    available_colors.append((i, colors_data[color_key]))
            
            if not available_colors:
                await interaction.response.send_message("Brak kolorów do edycji.", ephemeral=True)
                return
            
            # Tworzymy formularz edycji
            modal = ColorSelectionModal(available_colors)
            await interaction.response.send_modal(modal)
        except Exception as e:
            await interaction.response.send_message(f"Wystąpił błąd: {str(e)}", ephemeral=True)


# Widok edycji kolorów – przyciski jako cyfry (dla kolorów już ustawionych)
class EditColorView(View):
    def __init__(self, colors_data: dict, guild_id: int):
        super().__init__(timeout=180)
        self.guild_id = guild_id
        self.colors_data = colors_data or {}
        
        # Dodajemy przyciski dla każdego ustawionego koloru (od 1 do 10)
        number_emojis = {1:"1️⃣",2:"2️⃣",3:"3️⃣",4:"4️⃣",5:"5️⃣",6:"6️⃣",7:"7️⃣",8:"8️⃣",9:"9️⃣",10:"🔟"}
        for index in range(1, 11):
            if self.colors_data.get(f"hex_{index}"):
                self.add_item(
                    Button(
                        label=str(index),
                        emoji=number_emojis[index],
                        style=discord.ButtonStyle.primary,
                        custom_id=f"edit_{index}"
                    )
                )
        self.add_item(Button(label="BACK", style=discord.ButtonStyle.danger, custom_id="back_edit"))
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return True

# Modal, w którym użytkownik wpisze nowy kolor lub nadpisze stary
class ColorEditModal(Modal):
    def __init__(self, color_index: int):
        super().__init__(title=f"Edycja koloru {color_index}")
        self.color_index = color_index
        # self.add_item(InputText(label="Wprowadź kolor (np. #FFFFFF)", placeholder="#FFFFFF"))
    
    async def callback(self, interaction: discord.Interaction):
        new_color = self.children[0].value
        # Tu możesz dodać logikę aktualizacji w bazie, np.:
        # with db as db_session:
        #      db_session.update(model.select_class("select"), {"server_id": interaction.guild.id}, {f"hex_{self.color_index}": new_color})
        await interaction.response.send_message(f"Zaktualizowano kolor {self.color_index} na {new_color}", ephemeral=True)


# Modal do wyboru koloru i edycji wartości
class ColorSelectionModal(Modal):
    def __init__(self, available_colors):
        super().__init__(title="Edycja koloru")
        
        # Dodaj więcej logów
        logging.info(f"Tworzenie modalu z dostępnymi kolorami: {available_colors}")
        
        # Zamiast Select, używamy TextInput do podania numeru koloru
        self.color_index = TextInput(
            label="Numer koloru do edycji",
            placeholder="Wpisz numer od 1 do 10",
            style=discord.TextStyle.short,
            required=True,
            min_length=1,
            max_length=2
        )
        self.add_item(self.color_index)
        
        # Pole do wpisania nowej wartości koloru
        self.color_input = TextInput(
            label="Nowa wartość koloru",
            placeholder="#FFFFFF",
            style=discord.TextStyle.short,
            required=True
        )
        self.add_item(self.color_input)
        
        # Zachowujemy listę dostępnych kolorów jako atrybut klasy
        self.available_colors = {str(i): hex_value for i, hex_value in available_colors}
        logging.info(f"Dostępne kolory: {self.available_colors}")
    
    # Uproszczony callback - tylko potwierdź otrzymanie danych
    async def on_submit(self, interaction: discord.Interaction):
        logging.info("MODAL ON_SUBMIT: Rozpoczęcie wykonania")
        try:
            selected_index = self.color_index.value
            new_color_value = self.color_input.value
            logging.info(f"Otrzymane wartości: indeks={selected_index}, kolor={new_color_value}")
            
            await interaction.response.send_message(
                f"Pomyślnie odebrano dane: indeks={selected_index}, kolor={new_color_value}",
                ephemeral=True
            )
        except Exception as e:
            logging.error(f"BŁĄD W ON_SUBMIT: {str(e)}", exc_info=True)
            try:
                await interaction.response.send_message(f"Wystąpił błąd: {str(e)}", ephemeral=True)
            except:
                pass


class SetupCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    group = app_commands.Group(name="setup", description="Setup bot on your server")

    @group.command(name="select", description="Setup static colors on server")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def select(self, interaction: discord.Interaction) -> None:
        embed = Embed(title="Konfiguracja kolorów", color=4539717)

        try:
            await interaction.response.defer(ephemeral=True)
            with db as session:
                query_result = session.select(model.select_class("select"), {"server_id": interaction.guild.id})
            # Jeśli nie znaleziono danych, ustawiamy pusty słownik
            colors_data = query_result[0] if query_result else {}

            # W zależności od wyniku generujemy embed
            if not any(colors_data.values()):
                embed.description = "Brak ustawionych kolorów. Użyj przycisku CREATE aby dodać pierwszy."
            else:
                embed.description = "Aktualnie ustawione kolory:\n"
                for i in range(1, 11):
                    color_val = colors_data.get(f"hex_{i}")
                    if color_val:
                        embed.description += f"**{i}.** {color_val}\n"
                    else:
                        embed.description += f"**{i}.** -\n"

            view = SetupEmbedView(colors_data, interaction.guild.id)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        except Exception as e:
            embed.clear_fields()
            embed.description = cmd_messages['exception']
            await interaction.followup.send(embed=embed, ephemeral=True)
            self.bot.logger.critical(f"{interaction.user.name}[{interaction.user.id}] exception: {repr(e)}")

    @group.command(name="toprole", description="Setup top role for color roles")
    @app_commands.describe(role_name="Role name")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def toprole(self, interaction: discord.Interaction, role_name: discord.Role) -> None:
        embed: Embed = discord.Embed(title="", description=f"", color=4539717)
        try:
            await interaction.response.defer(ephemeral=True)

            pattern = re.compile(f"color-\\d{{18,19}}")
            top_role = discord.utils.get(interaction.guild.roles, id=role_name.id)

            with db as db_session:
                query = db_session.select(model.guilds_class("guilds"), {"server": interaction.guild.id})

            if top_role.position == 0:
                if query:
                    db.delete(model.guilds_class(f"guilds"), {"server": interaction.guild.id})
                embed.description = cmd_messages['toprole_reset']
            else:
                if query:
                    db.update(model.guilds_class(f"guilds"), {"server": interaction.guild.id},
                              {"role": role_name.id})
                else:
                    db.create(model.guilds_class(f"guilds"), {"server": interaction.guild.id, "role": role_name.id})

                embed.description = cmd_messages['toprole_set'].format(role_name.name)

                for role in interaction.guild.roles:
                    if pattern.match(role.name):
                        role = discord.utils.get(interaction.guild.roles, id=role.id)
                        await role.edit(position=max(1, top_role.position - 1))

                for i, static_role in enumerate(interaction.guild.roles, start=1):
                    if i > 5:
                        break
                    role = discord.utils.get(interaction.guild.roles, name=f"color-static-{i}")
                    if role:
                        await role.edit(position=top_role.position + 1)

        except discord.HTTPException as e:
            embed.clear_fields()
            if e.code == 50013:
                embed.description = cmd_messages['err_50013']
            else:
                embed.description = cmd_messages['err_http'].format(e.code, e.text)
            logging.critical(f"{interaction.user.name}[{interaction.user.id}] raise HTTP exception: {e.text}")

        except Exception as e:
            embed.clear_fields()
            embed.description = cmd_messages['exception']
            logging.critical(f"{interaction.user.name}[{interaction.user.id}] raise critical exception - {repr(e)}")

        finally:
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.followup.send(embed=embed)
            logging.info(
                f"{interaction.user.name}[{interaction.locale}] issued bot command: /setup toprole")

    @toprole.error
    @select.error
    async def command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            retry_time = datetime.now() + timedelta(seconds=error.retry_after)
            response = cmd_messages["cool_down"].format(int(retry_time.timestamp()))
            await interaction.response.send_message(response, ephemeral=True, delete_after=error.retry_after)

        elif isinstance(error, discord.app_commands.errors.MissingPermissions):
            embed: Embed = discord.Embed(title="", description=cmd_messages['no_permissions'],
                                         color=4539717, timestamp=datetime.now())
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SetupCog(bot))
