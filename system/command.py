from redbot.core import commands

# when i did this i thought there were a few commands with limited OSes... but not, only 1 command
# has limited OS support


class DynamicHelp(commands.Command):
    def __init__(self, *args, **kwargs):
        self.supported_system = kwargs.pop("supported_sys", True)  # unsupported sys is handled
        super().__init__(*args, **kwargs)

    @property
    def short_doc(self) -> str:
        if self.supported_system:
            return super().short_doc
        return "Not supported on this OS."

    def format_help_for_context(self, ctx: commands.Context) -> str:
        if self.supported_system:
            return super().format_help_for_context(ctx)
        return "Not supported on this OS.\n\n" + super().format_help_for_context(ctx)
