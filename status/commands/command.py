from redbot.core import commands

from status.core.consts import FEEDS
from status.vexutils.chat import inline_hum_list

SERVICE_LIST = inline_hum_list(tuple(FEEDS.keys()))


class DynamicHelp(commands.Command):
    """Append a dynamic list of available servies to the help."""

    def format_help_for_context(self, ctx: commands.Context) -> str:
        return super().format_help_for_context(ctx) + "\n\nAvailable services:\n" + SERVICE_LIST


class DynamicHelpGroup(commands.Group):
    """Append a dynamic list of avalible services to the help."""

    def format_help_for_context(self, ctx: commands.Context) -> str:
        return super().format_help_for_context(ctx) + "\n\nAvailable services:\n" + SERVICE_LIST

    def command(self, *args, **kwargs):
        return super().command(*args, **kwargs)
