# type:ignore
# until dpy2

import asyncio
from dataclasses import dataclass
from typing import Any, List, Optional

import discord
from redbot.core import commands

if discord.__version__.startswith("1"):
    raise RuntimeError("This requires discord.py 2.X")
from discord import ButtonStyle, Embed, Interaction, ui


@dataclass
class PredItem:
    """
    `ref` is what you want to be returned from the predicate if this button is clicked, though it
    cannot be None

    `label` and `style` are what the button will look like.

    `row` is optional if you want to change how it will look in Discord
    """

    ref: Any
    style: ButtonStyle
    label: str
    row: Optional[int] = None


class _PredView(ui.View):
    def __init__(self, timeout: Optional[float], author_id: int):
        super().__init__(timeout=timeout)
        self.ref: Any = None
        self.author_id = author_id

        self.pressed = asyncio.Event()

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id == self.author_id:
            return True

        await interaction.response.send_message(
            "You don't have have permission to do this.", ephemeral=True
        )
        return False


class _PredButton(ui.Button):
    def __init__(self, ref: Any, style: ButtonStyle, label: str, row: Optional[int] = None):
        super().__init__(style=style, label=label, row=row)
        self.ref = ref

    async def callback(self, interaction: Interaction):
        assert isinstance(self.view, _PredView)
        self.view.stop()
        self.view.ref = self.ref
        self.view.pressed.set()


async def wait_for_press(
    ctx: commands.Context,
    items: List[PredItem],
    content: Optional[str] = None,
    embed: Optional[Embed] = None,
    *,
    timeout: float = 180.0,
) -> Any:
    """Wait for a single button press with customisable buttons.

    Only the original author will be allowed to use this.

    Parameters
    ----------
    ctx : commands.Context
        Context to send message to
    items : List[PredItem]
        List of items to send as buttons
    content : Optional[str], optional
        Content of the message, by default None
    embed : Optional[Embed], optional
        Embed of the message, by default None
    timeout : float, optional
        Button timeout, by default 180.0

    Returns
    -------
    Any
        The defined reference of the clicked button

    Raises
    ------
    ValueError
        An empty list was supplied
    asyncio.TimeoutError
        A button was not pressed in time.
    """
    if not items:
        raise ValueError("The `items` argument cannot contain an empty list.")

    view = _PredView(timeout, ctx.author.id)  # type:ignore
    for i in items:
        button = _PredButton(i.ref, i.style, i.label, i.row)
        view.add_item(button)
    message = await ctx.send(content=content, embed=embed, view=view)

    await asyncio.wait_for(view.pressed.wait(), timeout=timeout)

    emptyview = ui.View()
    for i in items:
        button = ui.Button(
            style=i.style if i.ref == view.ref else ButtonStyle.gray,
            label=i.label,
            row=i.row,
            disabled=True,
        )
        emptyview.add_item(button)
    await message.edit(view=emptyview)
    emptyview.stop()

    return view.ref


async def wait_for_yes_no(
    ctx: commands.Context,
    content: Optional[str] = None,
    embed: Optional[Embed] = None,
    *,
    timeout: float = 180.0,
) -> bool:
    """Wait for a single button press of pre-defined yes and no buttons, returning True for yes
    and False for no.

    If you want to customise the buttons, I recommend you use the more generic `wait_for_press`.

    Only the original author will be allowed to use this.

    Parameters
    ----------
    ctx : commands.Context
        Context to send message to
    content : Optional[str], optional
        Content of the message, by default None
    embed : Optional[Embed], optional
        Embed of the message, by default None
    timeout : float, optional
        Button timeout, by default 180.0

    Returns
    -------
    bool
        True or False, depending on the clicked button.

    Raises
    ------
    asyncio.TimeoutError
        A button was not pressed in time.
    """
    view = _PredView(timeout, ctx.author.id)  # type:ignore
    view.add_item(_PredButton(True, ButtonStyle.blurple, "Yes"))
    view.add_item(_PredButton(False, ButtonStyle.blurple, "No"))

    message = await ctx.send(content=content, embed=embed, view=view)

    await asyncio.wait_for(view.pressed.wait(), timeout=timeout)

    emptyview = ui.View()
    emptyview.add_item(
        ui.Button(
            style=ButtonStyle.grey if view.ref is False else ButtonStyle.blurple,
            label="Yes",
            disabled=True,
        )
    )
    emptyview.add_item(
        ui.Button(
            style=ButtonStyle.grey if view.ref is True else ButtonStyle.blurple,
            label="No",
            disabled=True,
        )
    )
    await message.edit(view=emptyview)
    emptyview.stop()

    return view.ref
