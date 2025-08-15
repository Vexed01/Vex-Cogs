import discord


class PaginatedEmbedView(discord.ui.View):
    """A view for paginated embeds."""

    def __init__(self, pages: list[discord.Embed], expected_autor: int, timeout: float = 180.0):
        super().__init__(timeout=timeout)
        self.pages = pages
        self.current_page = 0
        self.expected_autor = expected_autor

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.primary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.pages[self.current_page])
        else:
            await interaction.response.defer()

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.primary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            await interaction.response.edit_message(embed=self.pages[self.current_page])
        else:
            await interaction.response.defer()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.expected_autor:
            return True

        await interaction.response.send_message(
            "You are not authorized to use this button because you didn't run the command.",
            ephemeral=True,
        )
        return False
