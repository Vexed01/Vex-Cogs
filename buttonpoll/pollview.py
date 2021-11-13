from typing import Optional

import discord
from discord.enums import ButtonStyle
from redbot.core.config import Config

from buttonpoll.poll import Poll


class OptionButton(discord.ui.Button):
    async def callback(self, interaction: discord.Interaction):
        assert isinstance(self.view, PollView)

        current_choice = await self.view.get_user_voter_vote(
            interaction.guild, interaction.user.id  # type:ignore
        )
        await self.view.config.guild(
            interaction.guild  # type:ignore
        ).poll_user_choices.set_raw(  # type:ignore
            self.view.poll_settings.unique_poll_id,
            interaction.user.id,  # type:ignore
            value=self.label,
        )

        if current_choice == self.label:
            msg = f"You're already voting for `{self.label}`!"
        if current_choice is not None:
            msg = f"You've already voted, so I've **changed** your vote to `{self.label}`."
        else:
            msg = f"You've voted for `{self.label}`."
        await interaction.response.send_message(msg, ephemeral=True)


class PollView(discord.ui.View):
    """View for an active poll. This is persistent-compatible."""

    def __init__(self, config: Config, poll_settings: Poll):
        super().__init__(timeout=None)
        for option in poll_settings.options:
            self.add_item(
                OptionButton(
                    style=option.style,
                    label=option.name,
                    custom_id=poll_settings.unique_poll_id[:50] + "_" + option.name[:50],
                )
            )

        self.poll_settings = poll_settings
        self.config = config

    async def get_user_voter_vote(self, guild: discord.Guild, user_id: int) -> Optional[str]:
        """Get the vote of a user in a poll."""
        return (
            (await self.config.guild(guild).poll_user_choices())
            .get(self.poll_settings.unique_poll_id, {})
            .get(str(user_id), None)  # everything is a string in config
        )

    @discord.ui.button(label="View my vote", custom_id="view_vote", style=ButtonStyle.grey, row=2)
    async def btn(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Show the user their current vote, if any."""
        choice = await self.get_user_voter_vote(
            interaction.guild, interaction.user.id  # type:ignore
        )
        if choice is None:
            await interaction.response.send_message("You haven't voted yet!", ephemeral=True)
        else:
            await interaction.response.send_message(
                f"You voted for {choice}. Change your vote be clicking a new button.",
                ephemeral=True,
            )
